import json


def _empty_payload(error_message=None):
    payload = {
        "invoice_number": None,
        "invoice_date": None,
        "invoice_time": None,
        "vendor_name": None,
        "subtotal": None,
        "discount": None,
        "tax": None,
        "total_amount": None,
        "items": []
    }
    if error_message:
        payload["error"] = error_message
    return payload


def clean_output(result: str):
    if not result:
        return _empty_payload("Empty model output")

    try:
        start = result.find("{")
        end = result.rfind("}") + 1
        if start == -1 or end <= start:
            return _empty_payload("Invalid JSON")

        json_str = result[start:end]
        parsed = json.loads(json_str)

        cleaned = _empty_payload()
        for key in cleaned:
            cleaned[key] = parsed.get(key)

        return cleaned
    except (json.JSONDecodeError, TypeError):
        return _empty_payload("Invalid JSON")
