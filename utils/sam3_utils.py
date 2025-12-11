import base64
import logging
import os
from io import BytesIO

import numpy as np
import requests
import torch
from PIL import Image

logger = logging.getLogger("seg.sam3_utils")

# Configuration from environment
SAM3_INFERENCE_URL = os.getenv(
    "SAM3_INFERENCE_URL", "http://sam3-inference:5001/invocations"
)
SAM3_TIMEOUT = int(os.getenv("SAM3_TIMEOUT", "120"))

logger.info(f"SAM3 Client initialized: {SAM3_INFERENCE_URL}")


class SAM3InferenceClient:
    """Client for SAM3 inference service"""

    def __init__(self, inference_url=SAM3_INFERENCE_URL, timeout=SAM3_TIMEOUT):
        self.inference_url = inference_url
        self.timeout = timeout
        logger.info(f"SAM3 API endpoint: {inference_url} (timeout: {timeout}s)")

    def _encode_image(self, image):
        """Encode PIL Image to base64 string"""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _decode_mask(self, encoded_mask):
        """Decode base64 string to numpy boolean mask"""
        mask_bytes = base64.b64decode(encoded_mask)
        mask_img = Image.open(BytesIO(mask_bytes))
        return np.array(mask_img) > 0

    def segment_with_boxes(self, image, boxes, threshold=0.5, mask_threshold=0.5):
        """
        Segment image using bounding box prompts

        Args:
            image: PIL Image
            boxes: List of [x1, y1, x2, y2] bounding boxes
            threshold: Confidence threshold (0.0-1.0)
            mask_threshold: Mask binarization threshold (0.0-1.0)

        Returns:
            dict: {'masks': [tensor, ...], 'scores': [float, ...]} or None
        """
        logger.info(f"Segmenting {len(boxes)} boxes on {image.size} image")

        # Prepare request - matches FastAPI server format
        payload = {
            "image": self._encode_image(image),
            "boxes": boxes,
            "threshold": threshold,
            "mask_threshold": mask_threshold,
        }

        # Call API with retry
        for attempt in range(3):
            try:
                response = requests.post(
                    self.inference_url, json=payload, timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()

                # Parse response - direct format from server
                if not result.get("success", False):
                    logger.error(f"API error: {result.get('error')}")
                    return None

                # Decode masks
                masks = [
                    torch.from_numpy(self._decode_mask(enc)) for enc in result["masks"]
                ]

                if masks:
                    logger.info(f"✓ Received {len(masks)} masks")
                    return {
                        "masks": masks,
                        "scores": result.get("scores", []),
                    }

                logger.warning("No masks in response")
                return None

            except requests.Timeout:
                logger.error(f"Timeout after {self.timeout}s (attempt {attempt+1}/3)")
                if attempt < 2:
                    continue

            except requests.RequestException as e:
                logger.error(f"Request failed: {e} (attempt {attempt+1}/3)")
                if attempt < 2:
                    continue

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                return None

        logger.error("All retry attempts failed")
        return None


def overlay_masks(image, masks, colors=None, opacity=0.5):
    """
    Overlay masks on image with colors

    Args:
        image: PIL Image
        masks: torch.Tensor [num_masks, H, W] or list of masks
        colors: List of RGB tuples or None (auto-generate)
        opacity: Float 0.0-1.0

    Returns:
        PIL Image with overlaid masks
    """
    import matplotlib

    image = image.convert("RGBA")

    # Convert masks to numpy
    if isinstance(masks, torch.Tensor):
        masks_np = masks.cpu().numpy()
    else:
        masks_np = np.array(masks)

    if len(masks_np.shape) == 2:
        masks_np = masks_np[np.newaxis, ...]

    n_masks = masks_np.shape[0]

    # Generate colors if needed
    if colors is None:
        cmap = matplotlib.colormaps.get_cmap("rainbow").resampled(n_masks)
        colors = [tuple(int(c * 255) for c in cmap(i)[:3]) for i in range(n_masks)]
    elif len(colors) == 1 and n_masks > 1:
        colors = colors * n_masks

    # Apply each mask
    for mask, color in zip(masks_np, colors):
        mask_binary = (mask > 0).astype(np.uint8) * 255
        mask_img = Image.fromarray(mask_binary, mode="L")
        overlay = Image.new("RGBA", image.size, color + (0,))
        alpha = mask_img.point(lambda v: int(v * opacity))
        overlay.putalpha(alpha)
        image = Image.alpha_composite(image, overlay)

    return image


def prepare_masks_for_overlay(results):
    """
    Prepare masks for overlay visualization

    Args:
        results: Dict with 'masks' key or list of masks

    Returns:
        torch.Tensor [num_masks, H, W]
    """
    if isinstance(results, list):
        masks = results
    elif isinstance(results, dict) and "masks" in results:
        masks = results["masks"]
    else:
        return None

    if not masks:
        return None

    if isinstance(masks, torch.Tensor):
        return masks.unsqueeze(0) if len(masks.shape) == 2 else masks
    elif isinstance(masks, list):
        return torch.stack(masks)
    else:
        tensor = torch.tensor(masks)
        return tensor.unsqueeze(0) if len(tensor.shape) == 2 else tensor


# ===== HELPER FUNCTIONS FOR CALLBACK REFACTORING =====

def extract_rectangles_by_class(shapes, all_annotation_class_store):
    """
    Extract and group rectangle annotations by class color.
    
    Args:
        shapes: List of shape annotations from figure
        all_annotation_class_store: List of annotation class metadata
        
    Returns:
        dict: {color: {"boxes": [[x0,y0,x1,y1], ...], "label": str}}
    """
    class_boxes = {}
    
    for shape in shapes:
        if shape.get("type") == "rect":
            color = shape.get("line", {}).get("color")
            if color:
                x0 = int(shape["x0"])
                y0 = int(shape["y0"])
                x1 = int(shape["x1"])
                y1 = int(shape["y1"])
                
                # Ensure coordinates are in correct order
                x_min = min(x0, x1)
                x_max = max(x0, x1)
                y_min = min(y0, y1)
                y_max = max(y0, y1)
                
                box = [x_min, y_min, x_max, y_max]
                
                if color not in class_boxes:
                    # Find label for this color
                    label = "Unknown"
                    for annotation_class in all_annotation_class_store:
                        if annotation_class["color"] == color:
                            label = annotation_class["label"]
                            break
                    class_boxes[color] = {"boxes": [], "label": label}
                
                class_boxes[color]["boxes"].append(box)
    
    return class_boxes


def load_and_prepare_image(image_data):
    """
    Load image data and convert to PIL Image format.
    
    Args:
        image_data: numpy array or other image format
        
    Returns:
        PIL.Image: Converted image
    """
    if isinstance(image_data, np.ndarray):
        # Normalize to 0-255 range
        low = np.percentile(image_data.ravel(), 1)
        high = np.percentile(image_data.ravel(), 99)
        image_data_normalized = np.clip(
            (image_data - low) / (high - low) * 255, 0, 255
        ).astype(np.uint8)
        
        # Convert grayscale to RGB if needed
        if len(image_data_normalized.shape) == 2:
            image_data_normalized = np.stack([image_data_normalized] * 3, axis=-1)
        
        return Image.fromarray(image_data_normalized)
    else:
        return image_data


def create_overlay_figure(overlay_image, image_shape):
    """
    Create Plotly figure patch with overlay image.
    
    Args:
        overlay_image: PIL Image with overlaid masks
        image_shape: Tuple (height, width) of original image
        
    Returns:
        dict: Figure patch with overlay configuration
    """
    from dash import Patch
    
    # Convert overlay image to base64 for display
    buffered = BytesIO()
    overlay_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    fig_patch = Patch()
    fig_patch["layout"]["images"] = [
        {
            "source": f"data:image/png;base64,{img_str}",
            "xref": "x",
            "yref": "y",
            "x": 0,
            "y": 0,
            "sizex": image_shape[1],
            "sizey": image_shape[0],
            "sizing": "stretch",
            "opacity": 0.5,
            "layer": "above",
        }
    ]
    
    return fig_patch


def convert_sam3_masks_to_numpy(
    all_masks, all_colors, class_results_summary, all_annotation_class_store, image_shape
):
    """
    Convert SAM3 masks to numpy array format matching manual annotations.
    
    Args:
        all_masks: List of all SAM3 masks
        all_colors: List of RGB colors for each mask
        class_results_summary: List of strings like "'label': N mask(s)"
        all_annotation_class_store: List of annotation class metadata
        image_shape: Tuple (height, width)
        
    Returns:
        np.ndarray: Mask array with shape (height, width) and class IDs
    """
    image_height, image_width = image_shape
    
    # Create a mapping from color to class_id and from label to class_id
    color_to_class_id = {}
    label_to_class_id = {}
    for idx, annotation_class in enumerate(all_annotation_class_store):
        color_to_class_id[annotation_class["color"]] = idx
        label_to_class_id[annotation_class["label"]] = idx
    
    # Create numpy mask for this slice
    slice_mask = np.full((image_height, image_width), fill_value=-1, dtype=np.int8)
    
    # Parse class_results_summary to get actual mask counts per class
    # Format: "'Class1': 3 mask(s)", "'Class2': 5 mask(s)"
    mask_idx = 0
    for summary in class_results_summary:
        # Extract label and count from summary string
        # Example: "'Class1': 3 mask(s)" -> label="Class1", num_masks=3
        parts = summary.split(":")
        label = parts[0].strip().strip("'\"")
        num_masks_str = parts[1].strip().split()[0]
        num_masks_for_class = int(num_masks_str)
        
        class_id = label_to_class_id.get(label, -1)
        if class_id == -1:
            logger.warning(f"Could not find class_id for label '{label}'")
            mask_idx += num_masks_for_class
            continue
        
        logger.info(
            f"Adding {num_masks_for_class} mask(s) for class '{label}' (id={class_id})"
        )
        
        # Get all masks for this class
        class_masks = all_masks[mask_idx : mask_idx + num_masks_for_class]
        mask_idx += num_masks_for_class
        
        # Combine all masks for this class into the slice mask
        for i, mask in enumerate(class_masks):
            mask_np = mask.cpu().numpy() if isinstance(mask, torch.Tensor) else mask
            # Handle both float and boolean masks
            if mask_np.dtype == np.float32 or mask_np.dtype == np.float64:
                mask_binary = mask_np > 0.5
            else:
                mask_binary = mask_np > 0
            
            pixels_added = np.sum(mask_binary)
            logger.info(
                f"  Mask {i+1}/{num_masks_for_class}: adding {pixels_added} pixels"
            )
            
            # Set pixels where mask is True to the class_id
            slice_mask[mask_binary] = class_id
    
    # Log final statistics
    unique_values, counts = np.unique(slice_mask, return_counts=True)
    logger.info("Final mask statistics:")
    for val, count in zip(unique_values, counts):
        if val == -1:
            logger.info(f"  Unlabeled: {count} pixels")
        else:
            class_label = all_annotation_class_store[val]["label"]
            logger.info(f"  Class {val} ({class_label}): {count} pixels")
    
    return slice_mask


def hex_to_rgb(hex_color):
    """
    Convert hex color to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., "#FF0000" or "FF0000")
        
    Returns:
        tuple: RGB values (r, g, b) where each is 0-255
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def segment_all_classes_with_sam3(
    image_pil, class_boxes, sam3_client, threshold=0.5, mask_threshold=0.5
):
    """
    Run SAM3 segmentation for all classes and collect results.
    
    Args:
        image_pil: PIL Image to segment
        class_boxes: Dict of {color: {"boxes": [[x0,y0,x1,y1], ...], "label": str}}
        sam3_client: SAM3InferenceClient instance
        threshold: Confidence threshold for SAM3
        mask_threshold: Mask binarization threshold for SAM3
        
    Returns:
        tuple: (all_masks, all_colors, class_results_summary)
            - all_masks: List of all mask tensors
            - all_colors: List of RGB tuples for each mask
            - class_results_summary: List of result strings for each class
        Returns (None, None, None) if no masks were generated
    """
    logger.info(f"Running SAM3 segmentation for {len(class_boxes)} class(es)...")
    
    all_masks = []
    all_colors = []
    class_results_summary = []

    for color, data in class_boxes.items():
        boxes = data["boxes"]
        label = data["label"]

        logger.info(f"Processing class '{label}' with {len(boxes)} box(es)...")

        # Run SAM3 for this class
        results = sam3_client.segment_with_boxes(
            image_pil,
            boxes,
            threshold=threshold,
            mask_threshold=mask_threshold,
        )

        if results is None or "masks" not in results or len(results["masks"]) == 0:
            logger.warning(f"SAM3 failed for class '{label}'")
            continue

        num_masks = len(results["masks"])
        logger.info(f"✓ Class '{label}': generated {num_masks} mask(s)")

        rgb_color = hex_to_rgb(color)

        # Add masks and colors for this class
        all_masks.extend(results["masks"])
        all_colors.extend([rgb_color] * num_masks)

        class_results_summary.append(f"'{label}': {num_masks} mask(s)")

    if not all_masks:
        logger.error("No masks generated for any class")
        return None, None, None
    
    logger.info(f"✓ Total masks generated: {len(all_masks)}")
    return all_masks, all_colors, class_results_summary


# Global client instance
sam3_segmenter = SAM3InferenceClient()