# VLM LLaVA Invoice Extractor

FastAPI service that uses LLaVA to extract invoice fields from image uploads.

## Project Structure

```
vlm_llava_project/
|- app/
|  |- main.py
|  |- routes.py
|- model/
|  |- llava_model.py
|- core/
|  |- prompt.py
|  |- extractor.py
|  |- cleaner.py
|- utils/
|  |- image_utils.py
|- config/
|  |- settings.py
|- tests/
|  |- test_api.py
|- requirements.txt
|- README.md
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run API

```bash
uvicorn app.main:app --reload
```

## Example Endpoint

- `POST /extract`
- Form field: `file` (image)

Example using curl:

```bash
curl -X POST "http://127.0.0.1:8000/extract" ^
  -H "accept: application/json" ^
  -H "Content-Type: multipart/form-data" ^
  -F "file=@invoice.png;type=image/png"
```

## Notes

- Default model: `llava-hf/llava-1.5-7b-hf`
- Device auto-selects `cuda` when available, otherwise `cpu`.
- Configure with environment variables: `MODEL_ID`, `DEVICE`, `MAX_TOKENS`.
