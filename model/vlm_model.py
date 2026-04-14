import json
import logging
import re

from model.hf_client import query_llava

logger = logging.getLogger(__name__)

MASTER_PROMPT = """You are an invoice OCR extraction engine.
Extract fields from the invoice image and return ONLY one valid JSON object.
Do not include markdown, explanation, labels, or extra keys.

Required fields:
- "vendor_name": (The shop or company name. Example: 'Acme Corp')
- "invoice_number": (The invoice or bill number. Example: 'INV-1234')
- "date": (The invoice date. Example: 'YYYY-MM-DD')
- "total_amount": (The final total amount to pay, including currency. Example: '$150.00')

Rules:
- If a field is missing, return "Not found".
- Preserve visible text exactly when possible.
- Prefer invoice number fields like "Invoice No", "Invoice Number", "Bill No".
- For total amount, prefer final payable total (Total / Grand Total / Amount Payable).

JSON output structure:
{
  "vendor_name": "...",
  "invoice_number": "...",
  "date": "...",
  "total_amount": "..."
}"""

def _default_result() -> dict:
    return {
        "vendor_name": "Not found",
        "invoice_number": "Not found",
        "date": "Not found",
        "total_amount": "Not found"
    }


def _normalize_value(value) -> str:
    """Clean and validate extracted values.
    
    Args:
        value: Raw extracted value from model or regex
        
    Returns:
        Cleaned string value or 'Not found' if invalid
    """
    if value is None:
        return "Not found"

    clean = str(value).strip()
    clean = re.sub(r'^(question|answer)\s*:\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+', ' ', clean).strip(" \t\n\r\"'")

    if not clean:
        return "Not found"

    bad_fragments = ["what is", "question :", "answer :", "extract", "invoice and return"]
    if any(fragment in clean.lower() for fragment in bad_fragments):
        return "Not found"

    return clean


def _extract_from_plain_text(text: str) -> dict:
    """Extract invoice fields from model response using regex patterns.
    
    Args:
        text: Raw model output text
        
    Returns:
        Dictionary with extracted vendor_name, invoice_number, date, total_amount
    """
    result = _default_result()
    if not text:
        return result

    patterns = {
        "vendor_name": [
            r'(?i)(?:vendor|seller|company|shop)\s*name\s*[:\-]\s*([^\n\r,]+)',
            r'(?i)^\s*([A-Z][A-Za-z0-9&.,\- ]{2,})\s*$'
        ],
        "invoice_number": [
            r'(?i)(?:invoice\s*(?:no|number)?|bill\s*(?:no|number)?)\s*[:#\-]\s*([A-Za-z0-9\-\/]+)'
        ],
        "date": [
            r'(?i)(?:invoice\s*date|date)\s*[:\-]\s*([0-9]{1,2}[-\/][0-9]{1,2}[-\/][0-9]{2,4}|[0-9]{4}[-\/][0-9]{1,2}[-\/][0-9]{1,2}|[A-Za-z]{3,9}\s+[0-9]{1,2},\s*[0-9]{4})'
        ],
        "total_amount": [
            r'(?i)(?:grand\s*total|amount\s*payable|total\s*amount|total)\s*[:\-]?\s*([\$\u20b9\u00a3\u20ac]?\s?[0-9][0-9,]*(?:\.[0-9]{1,2})?)'
        ]
    }

    for key, key_patterns in patterns.items():
        for pattern in key_patterns:
            match = re.search(pattern, text, flags=re.MULTILINE)
            if match:
                value = _normalize_value(match.group(1))
                if value != "Not found":
                    result[key] = value
                    break

    return result


def clean_output(text: str) -> dict:
    """Parse and clean model output into structured invoice fields.
    
    Attempts JSON parsing first, then regex extraction, falling back to plain-text extraction.
    
    Args:
        text: Raw model response
        
    Returns:
        Dictionary with extracted invoice fields
    """
    if not text:
        return _default_result()

    cleaned_text = re.sub(r'```json|```', '', text, flags=re.IGNORECASE).strip()
    cleaned_text = re.sub(r'(USER|ASSISTANT|QUESTION|ANSWER):', '', cleaned_text, flags=re.IGNORECASE)

    try:
        parsed_direct = json.loads(cleaned_text)
        result = _default_result()
        for key in result:
            result[key] = _normalize_value(parsed_direct.get(key))
        return result
    except Exception:
        pass

    match = re.search(r'\{[\s\S]*\}', cleaned_text)
    if match:
        try:
            parsed_block = json.loads(match.group(0))
            result = _default_result()
            for key in result:
                result[key] = _normalize_value(parsed_block.get(key))
            return result
        except Exception:
            logger.warning("LLaVA returned invalid JSON block; trying plain-text extraction")

    return _extract_from_plain_text(cleaned_text)


def extract_invoice_details(_image, image_bytes: bytes) -> dict:
    """Extract invoice details from image using LLaVA VLM.
    
    Args:
        _image: PIL Image object (for future use)
        image_bytes: Raw image bytes to process
        
    Returns:
        Dictionary with extracted vendor_name, invoice_number, date, total_amount
    """
    results = _default_result()

    try:
        logger.info("Attempting LLaVA extraction...")
        res = query_llava(image_bytes, MASTER_PROMPT)
        if "ERROR" not in res:
            parsed = clean_output(res)
            if any(value != "Not found" for value in parsed.values()):
                logger.info("LLaVA extraction successful")
                return parsed

            logger.warning("LLaVA response parsed but no concrete fields found")
            return results

        logger.error(f"LLaVA API error: {res}")
        return results
    except Exception as e:
        logger.error(f"LLaVA request failed: {e}")
        return results
