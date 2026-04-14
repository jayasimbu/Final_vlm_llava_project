import io

from PIL import Image
from fastapi import FastAPI, File, UploadFile

from model.vlm_model import extract_invoice_details
from utils.google_sheets import save_to_sheet
from utils.image_optimizer import optimize_image

app = FastAPI(
    title="VLM Invoice API",
    description="Image extraction API using Vision Language Models"
)

@app.post("/extract")
async def extract(file: UploadFile = File(...)) -> dict:
    """Extract invoice details from uploaded image and save to Google Sheets.
    
    Args:
        file: Image file to process (PNG, JPEG, AVIF, etc.)
        
    Returns:
        dict: Extraction results with status, extracted data, and sync status.
    """
    try:
        contents = await file.read()
        contents = optimize_image(contents)
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        data = extract_invoice_details(image, contents)
    except Exception as e:
        return {"status": "error", "error": str(e)}

    sheet_status = save_to_sheet(data)

    return {"status": "success", "data": data, "gsheets_synced": sheet_status}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
