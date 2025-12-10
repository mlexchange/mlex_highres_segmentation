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


# Global client instance
sam3_segmenter = SAM3InferenceClient()
