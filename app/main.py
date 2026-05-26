import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.cleaner import clean_output
from core.extractor import extract_data
from utils.image_utils import read_upload_image
from utils.invoice_qa import answer_invoice_question
from config.settings import MOCK_INFERENCE

app = FastAPI(
    title="VLM Invoice API (Final Clean Architecture)",
    description="Minimal Image-to-Excel API with Glassmorphic Frontend"
)


class AskRequest(BaseModel):
    question: str
    invoice_data: dict


class AskResponse(BaseModel):
    question: str
    answer: str

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a valid image file")

    image = await read_upload_image(file)
    raw = extract_data(image)
    clean = clean_output(raw)

    return {
        "status": "success",
        "data": clean,
        "mock_mode": MOCK_INFERENCE
    }


@app.post("/ask", response_model=AskResponse)
async def ask_invoice_question(payload: AskRequest):
    answer = answer_invoice_question(payload.invoice_data, payload.question)
    return {
        "question": payload.question,
        "answer": str(answer),
    }

# Serve index.html at root
@app.get("/")
async def read_index():
    index_path = os.path.join("app", "static", "index.html")
    return FileResponse(index_path)

# Mount static folder (ensure directory exists)
static_dir = os.path.join("app", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

