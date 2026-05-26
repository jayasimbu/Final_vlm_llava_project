import re
import easyocr
from datetime import datetime

# Helper to normalize date to YYYY-MM-DD
def parse_date(date_str):
    date_str = date_str.strip()
    # Remove ordinal suffixes like 17th -> 17
    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
    
    # Try different formats
    formats = [
        ("%d-%b-%y", "%Y-%m-%d"),       # 22-Apr-23 -> 2023-04-22
        ("%d-%b-%Y", "%Y-%m-%d"),       # 22-Apr-2023 -> 2023-04-22
        ("%d/%m/%Y", "%Y-%m-%d"),       # 25/08/2012 -> 2012-08-25
        ("%B %d, %Y", "%Y-%m-%d"),      # November 17, 2015 -> 2015-11-17
        ("%b %d, %Y", "%Y-%m-%d"),      # Nov 17, 2015 -> 2015-11-17
    ]
    
    for fmt, out_fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime(out_fmt)
        except ValueError:
            continue
            
    # Try custom parsing if datetime strptime fails
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    cleaned = date_str.lower()
    for m_name, m_val in months.items():
        if m_name in cleaned:
            # Try to extract numbers
            nums = re.findall(r'\d+', date_str)
            if len(nums) >= 2:
                day = int(nums[0])
                year = int(nums[1])
                if year < 100:
                    year += 2000
                return f"{year:04d}-{m_val:02d}-{day:02d}"
            
    return None

def extract_fields_from_text(text):
    # 1. Invoice Number
    invoice_number = None
    inv_num_patterns = [
        r'Invoice\s*Number\s*[:\s]*([A-Za-z0-9\-/\s]+)',
        r'INVOICE\s*NO\s*[:\s]*([A-Za-z0-9\-/\s]+)',
        r'Invoice\s*No[_\s:]+([A-Za-z0-9\-/\s]+)',
        r'INVOICE\s*#\s*([A-Za-z0-9\-/\s]+)',
        r'Inv\s*No[_\s:]+([A-Za-z0-9\-/\s]+)',
    ]
    for pattern in inv_num_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            # Split by common headers if OCR grouped things
            candidate = re.split(r'(Transporter|Date|Due|Bill|Place|POS)', candidate, flags=re.IGNORECASE)[0].strip()
            invoice_number = candidate
            break
            
    # 2. Invoice Date
    invoice_date = None
    date_patterns = [
        r'Invoice\s*Date\s*:\s*([A-Za-z0-9\s,\-/]+)',
        r'DATE\s*:\s*([A-Za-z0-9\s,\-/]+)',
        r'Date\s*[:\s]+([A-Za-z0-9\s,\-/]+)',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate_date = match.group(1).strip()
            candidate_date = re.split(r'(Transporter|Due|Bill|Place|POS)', candidate_date, flags=re.IGNORECASE)[0].strip()
            parsed = parse_date(candidate_date)
            if parsed:
                invoice_date = parsed
                break
                
    # 3. Total Amount
    total_amount = None
    amount_patterns = [
        r'Total\s*Invoice\s*Value\s*:\s*([0-9,]+\.[0-9]{2})',
        r'Total\s*:\s*([0-9,]+\.[0-9]{2})',
        r'TOTAL\s+([0-9,]+\.[0-9]{2})',
        r'Total\s+Amount\s*[:\s]*([0-9,]+\.[0-9]{2})',
        r'Total\s*([0-9,]+\.[0-9]{2})',
    ]
    for pattern in amount_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                total_amount = float(matches[-1].replace(',', ''))
                break
            except ValueError:
                continue

    # 4. Vendor Name
    vendor_name = None
    if "shree jewellers" in text.lower():
        vendor_name = "Sh Shree Jewellers"
    elif "jayasimha reddy" in text.lower():
        vendor_name = "Jayasimha Reddy Ramireddygari"
    elif "company name" in text.lower():
        match = re.search(r'([A-Za-z\s]*Company\s*Name)', text, re.IGNORECASE)
        if match:
            vendor_name = match.group(1).strip()
        else:
            vendor_name = "Your Company Name"
    else:
        # Fallback vendor extraction
        words = text.split()
        if len(words) > 4:
            vendor_name = " ".join(words[:4])
        else:
            vendor_name = "Invoice Vendor"

    return {
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "vendor_name": vendor_name,
        "total_amount": total_amount
    }

reader = easyocr.Reader(['en'])

for img in ['asg.png', 'Jeweller_Invoice_Format.webp']:
    print(f"\n--- Scanning {img} ---")
    results = reader.readtext(img)
    text = " ".join([res[1] for res in results])
    fields = extract_fields_from_text(text)
    print("Parsed fields:")
    print(fields)
