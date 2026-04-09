import fitz  # PyMuPDF
import io
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def convert_pdf_to_images(pdf_bytes: bytes, max_pages: int = 1):
    """
    Converts a PDF (bytes) into a list of PIL Images.
    By default, only converts the first page.
    """
    images = []
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        # Iterate through pages, limit to max_pages
        for i in range(min(len(doc), max_pages)):
            page = doc.load_page(i)
            # Higher matrix for better quality
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Convert pixmap to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
            
        doc.close()
    except Exception as e:
        logger.error(f"PDF to Image conversion failed: {str(e)}")
        
    return images

def get_first_page_as_bytes(pdf_bytes: bytes):
    """
    Converts the first page of a PDF to PNG bytes for VLM processing.
    """
    images = convert_pdf_to_images(pdf_bytes, max_pages=1)
    if not images:
        return None
        
    img_byte_arr = io.BytesIO()
    images[0].save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
