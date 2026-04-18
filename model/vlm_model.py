import json
from model.hf_client import query_llava, query_huggingface
from model.local_model import generate
from utils.ocr_extractor import extract_text_from_image_bytes, extract_invoice_fields_from_text
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUIRED_KEYS = [
    "vendor_name",
    "invoice_number",
    "date",
    "gst",
    "tax",
    "subtotal",
    "discount",
    "payment_method",
    "billing_address",
    "shipping_address",
    "items",
    "total_amount",
]

# 🔥 Expert Prompt for LLaVA 1.6
MASTER_PROMPT = """Analyze this invoice completely and extract:

- Vendor Name
- Invoice Number
- Date
- GST
- Tax
- Subtotal
- Discount
- Payment Method
- Billing Address
- Shipping Address
- Items Purchased (name, qty, price)
- Grand Total

Return JSON only. No extra text.
If a value is not visible, return "Not found".

{
    "vendor_name": "...",
    "invoice_number": "...",
    "date": "...",
    "gst": "...",
    "tax": "...",
    "subtotal": "...",
    "discount": "...",
    "payment_method": "...",
    "billing_address": "...",
    "shipping_address": "...",
    "items": [
        {
            "name": "...",
            "qty": "...",
            "price": "..."
        }
    ],
    "total_amount": "..."
}"""


def _default_invoice_payload():
        payload = {key: "Not found" for key in REQUIRED_KEYS}
        payload["items"] = []
        return payload

def clean_output(text):
    """
    🧹 Robust JSON Regex Parser
    """
    if not text:
        return None
        
    text = re.sub(r'(USER|ASSISTANT|QUESTION|ANSWER):', '', text, flags=re.IGNORECASE)
    
    # Try to find JSON block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        json_str = match.group(0)
        try:
            # Clean possible markdown artifacts inside or near the JSON
            json_str = json_str.replace('```json', '').replace('```', '')
            data = json.loads(json_str)
            
            # Ensure keys exist and sanitize values
            normalized = _default_invoice_payload()
            for key in REQUIRED_KEYS:
                normalized[key] = sanitize_field_value(key, data.get(key, normalized[key]))
            return normalized
        except json.JSONDecodeError as e:
            logger.warning(f"Regex found braces but JSON parsing failed: {e}. Raw text: {json_str[:100]}...")
            
    return None


def _strip_prompt_artifacts(text):
    """
    Remove common Q/A artifacts from local vision model responses.
    """
    if text is None:
        return ""

    value = str(text)
    value = re.sub(r'```(?:json)?|```', '', value, flags=re.IGNORECASE)
    value = re.sub(r'\b(user|assistant|question|answer)\b\s*[:\-]?', ' ', value, flags=re.IGNORECASE)
    value = re.sub(r'\s+', ' ', value).strip(' .,:;\n\t"\'')
    return value


def sanitize_field_value(field, raw_value):
    """
    Convert raw model output into predictable invoice field values.
    """
    text = _strip_prompt_artifacts(raw_value)
    if not text:
        return "Not found"

    lower_text = text.lower()

    if field == "items":
        if isinstance(raw_value, list):
            cleaned_items = []
            for item in raw_value:
                if not isinstance(item, dict):
                    continue
                name = _strip_prompt_artifacts(item.get("name", ""))
                qty = _strip_prompt_artifacts(item.get("qty", ""))
                price = _strip_prompt_artifacts(item.get("price", ""))
                if name:
                    cleaned_items.append({
                        "name": name,
                        "qty": qty if qty else "Not found",
                        "price": price if price else "Not found",
                    })
            return cleaned_items
        return []

    if field == "invoice_number":
        match = re.search(r'\b(?:inv[-_ ]?[A-Z0-9\-/]+|bill[-_ ]?[A-Z0-9\-/]+|#\d{3,}|\d{2,}[A-Z0-9\-/]*\d)\b', text, flags=re.IGNORECASE)
        return match.group(0) if match else "Not found"

    if field == "date":
        patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b',
            r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}\b'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(0)
        return "Not found"

    if field == "total_amount":
        matches = re.findall(r'[$€£₹]?\s*\d+(?:,\d{3})*(?:[\.,]\d{2})?', text)
        if matches:
            # Prefer the largest value if multiple numbers are present.
            def _to_float(v):
                cleaned = re.sub(r'[^0-9.,]', '', v).replace(',', '.')
                try:
                    return float(cleaned)
                except ValueError:
                    return -1.0
            return max(matches, key=_to_float).replace(' ', '')
        return "Not found"

    if field in {"gst", "tax", "subtotal", "discount"}:
        if field == "gst":
            match = re.search(r'\b\d{1,2}(?:\.\d+)?%\b', text)
            return match.group(0) if match else "Not found"
        match = re.search(r'[$€£₹]?\s*\d+(?:,\d{3})*(?:[\.,]\d{1,2})?', text)
        return match.group(0).replace(' ', '') if match else "Not found"

    if field == "payment_method":
        match = re.search(r'\b(upi|card|cash|net\s*banking|imps|neft|rtgs|wallet)\b', text, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper().replace(' ', '')
        return "Not found"

    if field in {"billing_address", "shipping_address"}:
        return text[:150] if len(text) >= 8 else "Not found"

    if field == "vendor_name":
        if any(token in lower_text for token in ["what", "answer", "question", "invoice number", "invoice date", "total amount"]):
            return "Not found"
        if len(text) < 2:
            return "Not found"
        return text[:80]

    return text


def merge_fields(primary, secondary):
    """
    Keep values from primary when present; fill gaps from secondary.
    """
    merged = {}
    for key in REQUIRED_KEYS:
        default_value = [] if key == "items" else "Not found"
        first = sanitize_field_value(key, primary.get(key, default_value))
        if key == "items":
            merged[key] = first if first else sanitize_field_value(key, secondary.get(key, []))
            continue
        if first != "Not found":
            merged[key] = first
        else:
            merged[key] = sanitize_field_value(key, secondary.get(key, default_value))
    return merged


def has_minimum_signal(data, min_fields=2):
    critical = ["vendor_name", "invoice_number", "date", "total_amount"]
    found = sum(1 for key in critical if data.get(key) and data.get(key) != "Not found")
    return found >= min_fields

def extract_invoice_details(image, image_bytes):
    """
    🔥 LLaVA Single-Call Extraction Flow
    """
    results = _default_invoice_payload()

    # 0. OCR-first pass (best for invoice number/date/amount on document images)
    ocr_text = extract_text_from_image_bytes(image_bytes)
    print("OCR TEXT:", ocr_text)
    ocr_fields = extract_invoice_fields_from_text(ocr_text)
    results = merge_fields(ocr_fields, results)
    if has_minimum_signal(results, min_fields=3):
        logger.info("✅ OCR extracted strong invoice signal.")
        return results

    # 1. Try LLaVA (Expert)
    try:
        logger.info("Trying LLaVA Master Prompt...")
        res = query_llava(image_bytes, MASTER_PROMPT)
        if "ERROR" not in res:
            parsed = clean_output(res)
            if parsed:
                logger.info("✅ LLaVA successfully extracted JSON.")
                return merge_fields(results, parsed)
            else:
                raise Exception("LLaVA returned invalid JSON format.")
        else:
            raise Exception(res)
    except Exception as e:
        logger.warning(f"⚠️ LLaVA failed: {e}. Trying BLIP-2 fallback...")
        
    # 2. Try BLIP Cloud Fallback
    try:
        res = query_huggingface(image_bytes, MASTER_PROMPT)
        if "ERROR" not in res:
            parsed = clean_output(res)
            if parsed:
                logger.info("✅ BLIP-2 successfully extracted JSON.")
                return merge_fields(results, parsed)
            else:
                raise Exception("BLIP-2 returned invalid JSON format.")
        else:
            raise Exception(res)
    except Exception as e_hf:
        logger.warning(f"⚠️ BLIP-2 fallback failed: {e_hf}. Trying Local fallback...")

    # 3. Try Local (Iterative as BLIP-base struggles with complex JSON)
    logger.info("Using Local Model (Iterative)")
    # Since local blip-base cannot generate JSON reliably, we prompt individually
    PROMPTS = {
        "vendor_name": "What is the shop or vendor name?",
        "invoice_number": "What is the invoice number?",
        "date": "What is the invoice date?",
        "gst": "What is the GST percentage?",
        "tax": "What is the total tax amount?",
        "subtotal": "What is the subtotal amount?",
        "discount": "What is the discount amount?",
        "payment_method": "What is the payment method or mode?",
        "billing_address": "What is the billing address?",
        "shipping_address": "What is the shipping address?",
        "total_amount": "What is the grand total amount?",
    }
    
    for key, prompt in PROMPTS.items():
        if results.get(key) != "Not found":
            continue
        try:
            res = generate(image, prompt)
            results[key] = sanitize_field_value(key, res)
        except Exception as local_e:
            logger.error(f"Local model failed for {key}: {local_e}")
            results[key] = "Not found"

    if not results.get("items"):
        try:
            item_response = generate(image, "List purchased items with quantity and unit price in JSON array format.")
            parsed_items = clean_output('{"items": ' + str(item_response) + '}')
            if parsed_items and isinstance(parsed_items.get("items"), list):
                results["items"] = parsed_items["items"]
        except Exception:
            results["items"] = []

    return results
