from PIL import Image
import io

def optimize_image(image_bytes, max_size=(500, 500), quality=50):
    """
    Resizes and compresses image bytes to prevent 'IncompleteRead' errors 
    during upload to Hugging Face Inference API.
    """
    try:
        # Load image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        
        # 1. Resize if too large (maintains aspect ratio)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # 2. Convert to JPEG for smallest file size
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # 3. Save back to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        optimized_bytes = buffer.getvalue()
        
        print(f"DEBUG: Image optimized from {len(image_bytes)} to {len(optimized_bytes)} bytes")
        return optimized_bytes
        
    except Exception as e:
        print(f"ERROR: Image optimization failed ({e}). Using original bytes.")
        return image_bytes
