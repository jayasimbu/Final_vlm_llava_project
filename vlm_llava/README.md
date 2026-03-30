# VLM (LLaVA) - Intelligent Invoice Analysis System

This module performs invoice understanding from images using LLaVA and supports both manual Q&A and automatic structured extraction.

## Project Structure

- `model/load_model.py`: loads processor and LLaVA model with device-aware precision
- `utils/image_preprocess.py`: image loading, validation, RGB conversion, resizing
- `prompts/templates.py`: dynamic prompt template construction
- `inference/generate_response.py`: single/batch QA, answer cleaning, structured JSON extraction
- `main.py`: CLI application
- `config.py`: central runtime configuration
- `tests/test_sample.py`: sample tests

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the CLI

```bash
python -m vlm_llava.main
```

CLI modes:

- `1 - Manual प्रश्न`: custom questions separated by `;`
- `2 - Auto Invoice Extraction`: predefined invoice fields in structured JSON

Manual mode example:

- Image path: `samples/invoice.jpg`
- Questions: `What is the total amount?;What is the invoice date?`

Auto mode example output:

```json
{
  "invoice_number": "INV-1023",
  "total_amount": "₹12450",
  "invoice_date": "12/02/2024",
  "vendor": "ABC Pvt Ltd",
  "tax": "₹450",
  "confidence": 0.93
}
```

## Run Tests

```bash
python -m pytest -q vlm_llava/tests
```

## Notes

- Default model: `llava-hf/llava-1.5-7b-hf`
- GPU is used automatically when available with fp16 for lower latency.
- Logs are written to `logs/app.log`.
- Auto extraction tries one-shot JSON first, then safely falls back to predefined question batch mode.
- Set environment variables to override defaults:
  - `VLM_MODEL_NAME`
  - `VLM_MAX_NEW_TOKENS`
  - `VLM_TEMPERATURE`
  - `VLM_TOP_P`
  - `VLM_IMAGE_SIZE`
  - `VLM_LOG_FILE`
