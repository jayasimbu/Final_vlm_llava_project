from fastapi import APIRouter, File, HTTPException, UploadFile

from core.cleaner import clean_output
from core.extractor import extract_data
from utils.image_utils import read_upload_image

router = APIRouter()


@router.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file")

    image = await read_upload_image(file)
    raw = extract_data(image)
    clean = clean_output(raw)

    return {"status": "success", "data": clean}
