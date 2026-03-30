from fastapi import FastAPI

from app.routes import router

app = FastAPI(title="VLM LLaVA Invoice Extractor")
app.include_router(router)
