def _clean_value(value):
    if value is None:
        return "Not found"
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned if cleaned else "Not found"
    return value


def answer_invoice_question(invoice_data, question):
    q = (question or "").strip().lower()
    if not q:
        return "Please ask a valid question."

    # Map tax to gst as they are used interchangeably here
    tax_val = invoice_data.get("tax")
    gst = _clean_value(invoice_data.get("gst") or tax_val)
    payment_method = _clean_value(invoice_data.get("payment_method"))
    invoice_number = _clean_value(invoice_data.get("invoice_number"))
    vendor_name = _clean_value(invoice_data.get("vendor_name"))
    invoice_date = _clean_value(invoice_data.get("invoice_date") or invoice_data.get("date"))
    invoice_time = _clean_value(invoice_data.get("invoice_time") or invoice_data.get("time"))
    total_amount = _clean_value(invoice_data.get("total_amount"))
    subtotal = _clean_value(invoice_data.get("subtotal"))
    discount = _clean_value(invoice_data.get("discount"))
    tax = _clean_value(tax_val)
    billing_address = _clean_value(invoice_data.get("billing_address"))
    shipping_address = _clean_value(invoice_data.get("shipping_address"))
    items = invoice_data.get("items") if isinstance(invoice_data.get("items"), list) else []

    if "gst" in q:
        return gst

    if "payment" in q or "mode" in q or "upi" in q or "card" in q or "cash" in q:
        return payment_method

    if "invoice number" in q or "bill number" in q:
        return invoice_number

    if "vendor" in q or "shop" in q or "seller" in q:
        return vendor_name

    if "date" in q:
        return invoice_date

    if "time" in q:
        return invoice_time

    if "subtotal" in q:
        return subtotal

    if "discount" in q:
        return discount

    if "tax" in q:
        return tax

    if "billing" in q or "bill to" in q:
        return billing_address

    if "shipping" in q or "ship to" in q:
        return shipping_address

    if "total" in q or "amount" in q:
        return total_amount

    if "how many item" in q or "item count" in q or "items purchased" in q:
        if not items:
            return "Not found"
        names = [str(it.get("name", "Item")).strip() for it in items if isinstance(it, dict)]
        names = [name for name in names if name]
        if not names:
            return str(len(items))
        return f"{len(items)} {', '.join(names)}"

    if "item" in q:
        if not items:
            return "Not found"
        summary = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "Item")).strip() or "Item"
            qty = str(item.get("qty", "Not found")).strip()
            price = str(item.get("price", "Not found")).strip()
            summary.append(f"{name} (qty: {qty}, price: {price})")
        return "; ".join(summary) if summary else "Not found"

    return (
        "I can answer GST, payment method, invoice number, vendor, date, time, subtotal, discount, tax, "
        "billing/shipping address, items, and total amount."
    )
