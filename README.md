# VLM Invoice Extractor

A production-grade FastAPI service that extracts structured invoice data (vendor name, invoice number, date, total amount) from images using LLaVA Vision Language Model and persists results to Google Sheets.

## Features

- Image-based invoice data extraction using LLaVA VLM
- Automatic image optimization and format conversion
- Google Sheets integration for data persistence
- Comprehensive error handling and logging
- RESTful API with automatic documentation

## Prerequisites

- Python 3.8+
- Hugging Face API token
- Google Sheets API credentials (service account JSON)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

1. Create `.env` file in project root:
   ```
   HF_TOKEN=your_huggingface_token_here
   ```

2. Place Google Sheets credentials at `credentials.json`

## Running the Server

### Using PowerShell
```powershell
.\start_server.ps1
```

### Using Python
```bash
python -m uvicorn app.main:app --reload
```

Server runs at `http://127.0.0.1:8000`

## API Usage

### Extract Invoice Data
```bash
curl -X POST "http://127.0.0.1:8000/extract" \
  -F "file=@invoice.jpg"
```

Response:
```json
{
  "status": "success",
  "data": {
    "vendor_name": "Company Name",
    "invoice_number": "INV-12345",
    "date": "2026-01-15",
    "total_amount": "$500.00"
  },
  "gsheets_synced": true
}
```

### Interactive API Docs
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Project Structure

```
.
├── app/
│   └── main.py              # FastAPI application
├── model/
│   ├── hf_client.py         # Hugging Face API client
│   └── vlm_model.py         # VLM extraction logic
├── utils/
│   ├── google_sheets.py     # Google Sheets integration
│   └── image_optimizer.py   # Image processing utilities
├── tests/
│   └── test_gsheets_connection.py
├── credentials.json         # Google service account (not tracked)
├── .env                     # Environment variables (not tracked)
└── start_server.ps1         # Server startup script
```

## Architecture

1. **API Layer** (`app/main.py`): FastAPI endpoint for file uploads
2. **Processing** (`model/`): Vision language model inference and data extraction
3. **Integration** (`utils/`): Image optimization and Google Sheets persistence
4. **Testing**: Connection validation for external services
