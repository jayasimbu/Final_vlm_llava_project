from fastapi import FastAPI, UploadFile, File
from model.vlm_model import extract_invoice_details
from utils.google_sheets import save_to_sheet
from utils.image_optimizer import optimize_image
from PIL import Image
import io

app = FastAPI(
    title="VLM Invoice API (Final Clean Architecture)",
    description="Minimal Image-to-Excel API without Frontend"
)

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    """
    💻 app/main.py (FINAL CLEAN VERSION)
    Accepts an image, extracts details via VLM, and saves to Excel.
    """
    contents = await file.read()
    
    try:
        # 🔥 Optimize image (Critical for HF stability)
        contents = optimize_image(contents)
        
        # 🔥 Convert to PIL Image for Local Model Fallback
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # HYBRID Extraction (HF Cloud -> Local Fallback)
        data = extract_invoice_details(image, contents)
    except Exception as e:
        print(f"Extraction failed: {e}")
        return {"error": str(e)}

    # 🔥 Save to Google Sheets (Cloud)
    sheet_status = save_to_sheet(data)

    return {
        "status": "success",
        "data": data,
        "gsheets_synced": sheet_status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
