import base64
import logging
import os
from io import BytesIO

import cv2
import numpy as np
import requests
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
            dict: {'masks': [np.ndarray, ...], 'scores': [float, ...]} or None
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

                # Decode masks to numpy arrays
                masks = [self._decode_mask(enc) for enc in result["masks"]]

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


# ===== HELPER FUNCTIONS FOR CALLBACKS =====


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


def convert_sam3_masks_to_numpy(
    all_masks,
    all_colors,
    class_results_summary,
    all_annotation_class_store,
    image_shape,
):
    """
    Convert SAM3 masks to numpy array format matching manual annotations.

    Args:
        all_masks: List of numpy arrays (boolean masks)
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
            mask_np = np.array(mask) if not isinstance(mask, np.ndarray) else mask
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


def masks_to_plotly_polygons(masks, class_color, min_area=100, epsilon_factor=0.002):
    """
    Convert SAM3 masks to Plotly polygon shapes.

    Args:
        masks: np.ndarray [num_masks, H, W] or list of masks
        class_color: Hex color string (e.g., "#FF0000")
        min_area: Minimum contour area in pixels
        epsilon_factor: Polygon simplification (0.001-0.01, lower=more detail)

    Returns:
        List of Plotly shape dicts for fig["layout"]["shapes"]
    """
    polygons = []

    # Convert to numpy
    if isinstance(masks, np.ndarray):
        masks_np = masks.astype(np.uint8)
    else:
        masks_np = np.array(masks).astype(np.uint8)

    if len(masks_np.shape) == 2:
        masks_np = masks_np[np.newaxis, ...]

    for mask in masks_np:
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            continue

        # Get largest contour
        contour = max(contours, key=cv2.contourArea)

        if cv2.contourArea(contour) < min_area:
            continue

        # Simplify polygon
        perimeter = cv2.arcLength(contour, True)
        epsilon = epsilon_factor * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)

        points = approx.squeeze().tolist()
        if not isinstance(points[0], list):
            points = [points]

        if len(points) < 3:
            continue

        # Build SVG path: M x0,y0 L x1,y1 ... Z
        path_parts = [f"M {points[0][0]},{points[0][1]}"]
        for x, y in points[1:]:
            path_parts.append(f"L {x},{y}")
        path_parts.append("Z")

        polygons.append(
            {
                "type": "path",
                "path": " ".join(path_parts),
                "fillcolor": class_color,
                "fillrule": "evenodd",
                "line": {"color": class_color},
                "editable": True,
            }
        )

    return polygons


def segment_all_classes_to_polygons(
    image_pil, class_boxes, sam3_client, threshold=0.5, mask_threshold=0.5
):
    """
    Run SAM3 and return BOTH polygons and masks.

    Returns:
        Tuple of (all_polygons, all_masks, all_colors, class_results_summary) or (None, None, None, None)
        - all_polygons: List of Plotly shape dicts (for UI display)
        - all_masks: List of numpy arrays (for mask conversion)
        - all_colors: List of hex colors (for mask conversion)
        - class_results_summary: List of result strings
    """
    logger.info(f"Generating polygons for {len(class_boxes)} class(es)...")

    all_polygons = []
    all_masks = []
    all_colors = []
    class_results_summary = []

    for color, data in class_boxes.items():
        boxes = data["boxes"]
        label = data["label"]

        logger.info(f"Processing '{label}' ({len(boxes)} box(es))...")

        results = sam3_client.segment_with_boxes(
            image_pil, boxes, threshold=threshold, mask_threshold=mask_threshold
        )

        if results is None or "masks" not in results or len(results["masks"]) == 0:
            logger.warning(f"SAM3 failed for '{label}'")
            continue

        # Convert to polygons for UI
        class_polygons = masks_to_plotly_polygons(results["masks"], class_color=color)

        # Keep original masks for Tiled export
        num_masks = len(results["masks"])

        logger.info(
            f"✓ '{label}': {len(class_polygons)} polygon(s), {num_masks} mask(s)"
        )

        all_polygons.extend(class_polygons)
        all_masks.extend(results["masks"])
        all_colors.extend([color] * num_masks)
        class_results_summary.append(f"'{label}': {len(class_polygons)} polygon(s)")

    if not all_polygons:
        return None, None, None, None

    logger.info(f"✓ Total: {len(all_polygons)} polygon(s), {len(all_masks)} mask(s)")
    return all_polygons, all_masks, all_colors, class_results_summary


# Global client instance
sam3_segmenter = SAM3InferenceClient()
