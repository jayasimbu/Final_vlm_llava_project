import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)

def optimize_image(image_bytes: bytes, max_size: tuple = (500, 500), quality: int = 50) -> bytes:
    """Resize and compress image to prevent API errors and reduce bandwidth.
    
    Converts RGBA/palette modes to RGB and applies quality compression.
    Falls back to original image on failure.
    
    Args:
        image_bytes: Raw image data
        max_size: Maximum (width, height) in pixels
        quality: JPEG quality (1-100)
        
    Returns:
        Optimized image bytes or original bytes if optimization fails
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        optimized_bytes = buffer.getvalue()

        return optimized_bytes

    except Exception as e:
        logger.warning(f"Image optimization failed: {e}. Using original image.")
        return image_bytes
