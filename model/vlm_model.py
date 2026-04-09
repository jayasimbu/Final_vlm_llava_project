import json
from model.hf_client import query_llava, query_huggingface
from model.local_model import generate
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔥 Expert Prompt for LLaVA 1.6
MASTER_PROMPT = """Extract the following details from this invoice and return ONLY a valid JSON object. Do not include any explanations, greetings, or markdown formatting outside of the JSON block.

Required fields:
- "vendor_name": (The shop or company name. Example: 'Acme Corp')
- "invoice_number": (The invoice or bill number. Example: 'INV-1234')
- "date": (The invoice date. Example: 'YYYY-MM-DD')
- "total_amount": (The final total amount to pay, including currency. Example: '$150.00')

If a field is missing, use "Not found" as its value.

JSON output structure:
{
  "vendor_name": "...",
  "invoice_number": "...",
  "date": "...",
  "total_amount": "..."
}"""

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
            
            # Ensure keys exist
            for key in ["vendor_name", "invoice_number", "date", "total_amount"]:
                if key not in data:
                    data[key] = "Not found"
            return data
        except json.JSONDecodeError as e:
            logger.warning(f"Regex found braces but JSON parsing failed: {e}. Raw text: {json_str[:100]}...")
            
    return None

def extract_invoice_details(image, image_bytes):
    """
    🔥 LLaVA Single-Call Extraction Flow
    """
    results = {
        "vendor_name": "Not found",
        "invoice_number": "Not found",
        "date": "Not found",
        "total_amount": "Not found"
    }

    # 1. Try LLaVA (Expert)
    try:
        logger.info("Trying LLaVA Master Prompt...")
        res = query_llava(image_bytes, MASTER_PROMPT)
        if "ERROR" not in res:
            parsed = clean_output(res)
            if parsed:
                logger.info("✅ LLaVA successfully extracted JSON.")
                return parsed
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
                return parsed
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
        "total_amount": "What is the total amount?"
    }
    
    for key, prompt in PROMPTS.items():
        try:
            res = generate(image, prompt)
            res = re.sub(r'(USER|ASSISTANT|QUESTION|ANSWER):', '', res, flags=re.IGNORECASE).strip()
            results[key] = res if len(res) >= 3 else "Not found"
        except Exception as local_e:
            logger.error(f"Local model failed for {key}: {local_e}")
            results[key] = "Not found"

    return results
