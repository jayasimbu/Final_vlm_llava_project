import io

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError


async def read_upload_image(file: UploadFile):
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return image
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Unable to read image") from exc
