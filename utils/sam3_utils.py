import os
import logging
import torch
import numpy as np
import matplotlib
from PIL import Image
from transformers import Sam3Model, Sam3Processor

# Configure logger
logger = logging.getLogger("seg.sam3_utils")

# Authenticate with Hugging Face if token is provided
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    try:
        from huggingface_hub import login
        login(token=HF_TOKEN)
        logger.info("Successfully authenticated with Hugging Face")
    except Exception as e:
        logger.warning(f"Failed to authenticate with Hugging Face: {e}")

# Get device - prefer CUDA, fall back to MPS, then CPU
def get_device():
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    return "cpu"

DEVICE = get_device()
SAM_MODEL_NAME = os.getenv("SAM_MODEL_NAME", "facebook/sam3")

logger.info(f"SAM using device: {DEVICE}")
logger.info(f"SAM model name: {SAM_MODEL_NAME}")


class SAM3Segmenter:
    """
    Wrapper for SAM3 segmentation with support for bbox and point prompts.
    Model is loaded lazily on first use to prevent worker timeout.
    """
    
    def __init__(self):
        self.device = DEVICE
        self.model = None
        self.processor = None
        self._loading = False
        self._load_failed = False
        logger.info("SAM3Segmenter initialized (model will load on first use)")
        
    def load_model(self):
        """Load SAM3 model and processor (lazy loading on first use)"""
        if self.model is not None:
            return True
        
        if self._load_failed:
            logger.error("Previous model load failed, skipping retry")
            return False
        
        if self._loading:
            logger.warning("Model is already being loaded by another request")
            return False
            
        try:
            self._loading = True
            logger.info("=" * 80)
            logger.info(f"Loading SAM3 model on {self.device}...")
            logger.info("This may take 30-60 seconds on first load...")
            logger.info("=" * 80)
            
            self.model = Sam3Model.from_pretrained(SAM_MODEL_NAME).to(self.device)
            self.processor = Sam3Processor.from_pretrained(SAM_MODEL_NAME)
            
            logger.info("=" * 80)
            logger.info("SAM3 model loaded successfully!")
            logger.info("=" * 80)
            return True
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"Error loading SAM3 model: {e}", exc_info=True)
            logger.error("=" * 80)
            self.model = None
            self.processor = None
            self._load_failed = True
            return False
            
        finally:
            self._loading = False
    
    def segment_with_boxes(self, image, boxes, threshold=0.5, mask_threshold=0.5):
        """
        Segment using bounding boxes
        
        Args:
            image: PIL Image
            boxes: list of [x1, y1, x2, y2] in pixel coordinates
            threshold: confidence threshold for mask selection
            mask_threshold: threshold for binarizing masks
            
        Returns: 
            dict with 'masks', 'scores', 'boxes' keys
            - masks: list of torch.Tensor masks, one per input box
            - scores: list of confidence scores
            - boxes: list of refined bounding boxes
        """
        logger.info("=" * 80)
        logger.info("=== SAM3 segment_with_boxes called ===")
        logger.info("=" * 80)
        
        # === DETAILED INPUT LOGGING ===
        logger.info("INPUT DETAILS:")
        logger.info(f"  Image type: {type(image)}")
        logger.info(f"  Image size: {image.size if hasattr(image, 'size') else 'N/A'}")
        logger.info(f"  Image mode: {image.mode if hasattr(image, 'mode') else 'N/A'}")
        logger.info(f"  Threshold: {threshold}")
        logger.info(f"  Mask threshold: {mask_threshold}")
        logger.info(f"  Number of boxes: {len(boxes)}")
        logger.info(f"  Bounding boxes:")
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            width = x2 - x1
            height = y2 - y1
            logger.info(f"    Box {i}: [x1={x1}, y1={y1}, x2={x2}, y2={y2}]")
            logger.info(f"           Size: {width}x{height} pixels")
            logger.info(f"           Area: {width * height} pixels")
        logger.info("=" * 80)
        
        if not self.load_model():
            logger.error("Failed to load model")
            return None
            
        try:
            logger.info("STEP 1: Processing inputs...")
            
            # Create labels list - one label per box (all positive)
            box_labels = [1] * len(boxes)
            
            logger.info(f"  Input boxes: {boxes}")
            logger.info(f"  Box labels: {box_labels}")
            
            inputs = self.processor(
                images=image,
                input_boxes=[boxes],  # Wrap in list for batch dimension
                input_boxes_labels=[box_labels],  # One label per box
                return_tensors="pt"
            ).to(self.device)
            
            logger.info(f"  Processor created inputs with keys: {list(inputs.keys())}")
            if "original_sizes" in inputs:
                logger.info(f"  Original sizes: {inputs['original_sizes']}")
            if "pixel_values" in inputs:
                logger.info(f"  Pixel values shape: {inputs['pixel_values'].shape}")
            if "input_boxes" in inputs:
                logger.info(f"  Input boxes shape: {inputs['input_boxes'].shape}")
            
            logger.info("STEP 2: Running SAM3 inference...")
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            logger.info(f"  Model outputs type: {type(outputs)}")
            if hasattr(outputs, 'keys'):
                logger.info(f"  Output keys: {list(outputs.keys())}")
            
            logger.info("STEP 3: Post-processing masks...")
            
            # Post-process to get masks
            results = self.processor.post_process_instance_segmentation(
                outputs,
                threshold=threshold,
                mask_threshold=mask_threshold,
                target_sizes=inputs.get("original_sizes").tolist()
            )[0]  # Get first (and only) batch item
            
            logger.info(f"  Results type: {type(results)}")
            logger.info(f"  Results keys: {list(results.keys())}")
            
            # === DETAILED OUTPUT LOGGING ===
            logger.info("=" * 80)
            logger.info("OUTPUT DETAILS:")
            
            if 'masks' in results and len(results['masks']) > 0:
                masks = results['masks']
                logger.info("=" * 80)
                logger.info(f"✓ Successfully generated {len(masks)} mask(s)")
                logger.info("=" * 80)
                
                return results
            else:
                logger.warning("=" * 80)
                logger.warning("✗ No masks generated!")
                logger.warning("=" * 80)
                return None
                
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"✗ Error in box segmentation: {e}", exc_info=True)
            logger.error("=" * 80)
            return None


def overlay_masks(image, masks, colors=None, opacity=0.5):
    """
    Overlay masks on image with different colors
    
    Args:
        image: PIL Image
        masks: torch.Tensor of shape [num_masks, H, W] or list of masks
        colors: Optional list of RGB tuples (one per mask). If only one color 
                provided, it will be used for all masks.
        opacity: Float between 0 and 1 for mask transparency
    
    Returns:
        PIL Image with masks overlaid
    """
    logger.info("=" * 80)
    logger.info("=== overlay_masks called ===")
    logger.info(f"  Image size: {image.size}")
    logger.info(f"  Masks type: {type(masks)}")
    logger.info(f"  Masks shape: {masks.shape if hasattr(masks, 'shape') else 'N/A'}")
    logger.info(f"  Opacity: {opacity}")
    
    image = image.convert("RGBA")
    
    # Convert masks to numpy
    if isinstance(masks, torch.Tensor):
        masks_np = masks.cpu().numpy()
    else:
        masks_np = np.array(masks)
    
    # Ensure masks are in the right shape [num_masks, H, W]
    if len(masks_np.shape) == 2:
        masks_np = masks_np[np.newaxis, ...]  # Add batch dimension
    
    n_masks = masks_np.shape[0]
    logger.info(f"  Number of masks: {n_masks}")
    
    # Generate colors if not provided
    if colors is None:
        cmap = matplotlib.colormaps.get_cmap("rainbow").resampled(n_masks)
        colors = [
            tuple(int(c * 255) for c in cmap(i)[:3])
            for i in range(n_masks)
        ]
        logger.info(f"  Generated {len(colors)} rainbow colors")
    else:
        # If only one color provided but multiple masks, repeat it
        if len(colors) == 1 and n_masks > 1:
            colors = colors * n_masks
            logger.info(f"  Repeated single color {n_masks} times: {colors[0]}")
        logger.info(f"  Using {len(colors)} colors")
    
    logger.info(f"  Overlaying {n_masks} masks with {len(colors)} colors")
    
    # Apply each mask
    for i, (mask, color) in enumerate(zip(masks_np, colors)):
        # Convert to uint8 binary mask
        mask_binary = (mask > 0).astype(np.uint8) * 255
        true_pixels = (mask > 0).sum()
        
        logger.info(f"  Mask {i}: color={color}, true_pixels={true_pixels}")
        
        # Create PIL image from mask
        mask_img = Image.fromarray(mask_binary, mode='L')
        
        # Create colored overlay
        overlay = Image.new("RGBA", image.size, color + (0,))
        
        # Set alpha channel based on mask with specified opacity
        alpha = mask_img.point(lambda v: int(v * opacity))
        overlay.putalpha(alpha)
        
        # Composite onto image
        image = Image.alpha_composite(image, overlay)
    
    logger.info("✓ Overlay complete")
    logger.info("=" * 80)
    return image


def prepare_masks_for_overlay(results):
    """
    Prepare masks from SAM3 results for overlay
    Converts torch tensors to a stacked tensor if needed
    
    Args:
        results: Dict with 'masks' key containing list of masks
    
    Returns:
        torch.Tensor of shape [num_masks, H, W]
    """
    if results is None or 'masks' not in results:
        return None
    
    masks = results['masks']
    
    if isinstance(masks, torch.Tensor):
        # Already a tensor, ensure 3D shape
        if len(masks.shape) == 2:
            return masks.unsqueeze(0)  # Add batch dimension
        return masks
    elif isinstance(masks, list):
        # Stack list of tensors
        return torch.stack(masks)
    else:
        # Convert to tensor
        tensor = torch.tensor(masks)
        if len(tensor.shape) == 2:
            return tensor.unsqueeze(0)
        return tensor


# Global instance - model will load lazily on first use
sam3_segmenter = SAM3Segmenter()
logger.info("Global sam3_segmenter instance created (lazy loading enabled)")