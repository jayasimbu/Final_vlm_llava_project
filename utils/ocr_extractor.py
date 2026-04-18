import re
import io
import os
import numpy as np
from PIL import Image, ImageEnhance


_EASYOCR_READER = None


def _configure_tesseract_path(pytesseract_module):
    """Configure tesseract executable path on Windows when PATH is not set."""
    if os.name != "nt":
        return

    candidates = [
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            pytesseract_module.pytesseract.tesseract_cmd = candidate
            return


def rotate_image(image):
    return image.rotate(90, expand=True)


def preprocess_image(image, angle=0, contrast=2.5, threshold=None):
    # rotate first
    image = image.rotate(angle, expand=True)

    # grayscale
    image = image.convert("L")

    # contrast boost
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(contrast)

    # threshold is optional; handwriting can degrade with aggressive binarization
    if threshold is not None:
        image = image.point(lambda x: 0 if x < threshold else 255)

    return image


def _ocr_quality_score(text):
    if not text:
        return -1

    cleaned = text.strip()
    if not cleaned:
        return -1

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    alpha = len(re.findall(r"[A-Za-z]", cleaned))
    digits = len(re.findall(r"\d", cleaned))
    words = len(re.findall(r"\b[A-Za-z]{2,}\b", cleaned))
    key_hits = len(re.findall(r"invoice|date|total|amount|subtotal|gst|tax|qty|quantity|bill", cleaned, flags=re.IGNORECASE))
    symbol_noise = len(re.findall(r"[|`~^_]{2,}", cleaned))

    return (len(lines) * 2) + alpha + digits + (words * 2) + (key_hits * 10) - (symbol_noise * 5)


def _to_cv_bgr(image):
    rgb = np.array(image.convert("RGB"))
    return rgb[:, :, ::-1].copy()


def _to_pil_image(cv_bgr):
    rgb = cv_bgr[:, :, ::-1]
    return Image.fromarray(rgb)


def _order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def _four_point_transform(image, pts):
    import cv2

    rect = _order_points(pts)
    (tl, tr, br, bl) = rect

    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = max(int(width_a), int(width_b), 1)

    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = max(int(height_a), int(height_b), 1)

    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1],
    ], dtype="float32")

    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, matrix, (max_width, max_height))


def _correct_document_perspective(image):
    try:
        import cv2
    except Exception:
        return image

    try:
        cv_img = _to_cv_bgr(image)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blur, 50, 150)

        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        page_contour = None
        for contour in contours[:10]:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approx) == 4:
                page_contour = approx.reshape(4, 2)
                break

        if page_contour is None:
            return image

        warped = _four_point_transform(cv_img, page_contour)
        return _to_pil_image(warped)
    except Exception:
        return image


def _deskew_document(image):
    try:
        import cv2
    except Exception:
        return image

    try:
        cv_img = _to_cv_bgr(image)
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        coords = np.column_stack(np.where(binary > 0))
        if coords.size == 0:
            return image

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        if abs(angle) < 0.5:
            return image

        (h, w) = cv_img.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(cv_img, matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return _to_pil_image(rotated)
    except Exception:
        return image


def _get_easyocr_reader():
    global _EASYOCR_READER
    if _EASYOCR_READER is not None:
        return _EASYOCR_READER

    import easyocr
    _EASYOCR_READER = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _EASYOCR_READER


def _easyocr_text(image):
    try:
        reader = _get_easyocr_reader()
        arr = np.array(image.convert("RGB"))
        results = reader.readtext(arr, detail=1, paragraph=False)
        if not results:
            return ""

        segments = []
        for item in results:
            if len(item) >= 2:
                segments.append(str(item[1]).strip())
        return "\n".join(segment for segment in segments if segment)
    except Exception:
        return ""


def _needs_easyocr(best_text, best_score):
    if best_score < 80:
        return True
    alnum = len(re.findall(r"[A-Za-z0-9]", best_text or ""))
    key_hits = len(re.findall(r"invoice|date|total|amount|subtotal|gst|tax|qty|quantity|bill", best_text or "", flags=re.IGNORECASE))
    return alnum < 35 or key_hits == 0


def extract_text(image):
    import pytesseract

    _configure_tesseract_path(pytesseract)

    corrected = _correct_document_perspective(image)
    corrected = _deskew_document(corrected)

    candidates = []
    sources = [corrected, image]

    for source in sources:
        for angle in (0, 90, 180, 270):
            for contrast in (1.8, 2.4):
                for threshold in (None, 150, 170):
                    processed = preprocess_image(source, angle=angle, contrast=contrast, threshold=threshold)
                    for psm in (6, 11):
                        try:
                            text = pytesseract.image_to_string(processed, config=f"--oem 3 --psm {psm}")
                        except Exception:
                            text = ""
                        candidates.append((text, _ocr_quality_score(text), "tesseract"))

    if not candidates:
        return ""

    best_text, best_score, _ = max(candidates, key=lambda x: x[1])

    if _needs_easyocr(best_text, best_score):
        easy_text = _easyocr_text(corrected)
        easy_score = _ocr_quality_score(easy_text)
        if easy_score > best_score:
            return easy_text

    return best_text


def extract_text_from_image_bytes(image_bytes):
    """Best-effort OCR text extraction. Returns empty string if OCR is unavailable."""
    try:
        import pytesseract
        _configure_tesseract_path(pytesseract)
    except Exception:
        return ""

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        text = extract_text(img)
        return text.strip()
    except Exception:
        return ""


def _first_match(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip() if match.groups() else match.group(0).strip()
    return "Not found"


def _pick_vendor_name(lines):
    blocked = {
        "invoice",
        "tax invoice",
        "bill",
        "service record",
        "not found",
    }
    for line in lines[:12]:
        normalized = line.strip()
        if len(normalized) < 3:
            continue
        lower = normalized.lower()
        if lower in blocked:
            continue
        if re.search(r"invoice|date|total|amount|qty|quantity|gst|tax", lower):
            continue
        if len(re.findall(r"[A-Za-z]", normalized)) < 3:
            continue
        return normalized[:80]
    return "Not found"


def _extract_items_from_text(text):
    items = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Best-effort line parsing for rows like: ItemName   2   499.00
    for line in lines:
        if any(skip in line.lower() for skip in [
            "invoice", "date", "total", "subtotal", "gst", "tax", "discount", "address", "payment",
        ]):
            continue

        match = re.search(r"^([A-Za-z][A-Za-z0-9 ._\-/()]+?)\s+(\d{1,3})\s+([₹$€£]?\s*\d+(?:,\d{3})*(?:[\.,]\d{1,2})?)$", line)
        if match:
            items.append({
                "name": match.group(1).strip(),
                "qty": match.group(2).strip(),
                "price": match.group(3).replace(" ", "").strip(),
            })

    return items


def extract_invoice_fields_from_text(text):
    if not text:
        return {
            "vendor_name": "Not found",
            "invoice_number": "Not found",
            "date": "Not found",
            "gst": "Not found",
            "tax": "Not found",
            "subtotal": "Not found",
            "discount": "Not found",
            "payment_method": "Not found",
            "billing_address": "Not found",
            "shipping_address": "Not found",
            "items": [],
            "total_amount": "Not found",
        }

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    vendor_name = _pick_vendor_name(lines)

    invoice_match = re.search(
        r"(Invoice\s*(No|#|Number)?[:\-\s]*)([A-Z0-9\-\/]+)",
        text,
        flags=re.IGNORECASE,
    )
    if invoice_match:
        invoice_number = invoice_match.group(3).strip()
    else:
        invoice_number = _first_match(text, [
            r"\b(#\d{3,}|[A-Z]{2,}\-\d{2,}|\d{4,})\b",
        ])

    date = _first_match(text, [
        r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        r"(?:date\s*[:\-]?\s*)(\d{4}-\d{2}-\d{2})",
        r"\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})\b",
        r"\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b",
    ])

    amount_match = re.search(
        r"(Total|Grand\s*Total|Amount\s*Due)[:\s₹$€£]*([\d,]+(?:[\.,]\d{2})?)",
        text,
        flags=re.IGNORECASE,
    )
    if amount_match:
        total_amount = amount_match.group(2).strip()
    else:
        total_amount = _first_match(text, [
            r"([\$€£₹]?\d+(?:,\d{3})*(?:\.\d{2}))",
            r"([\$€£₹]?\d+(?:,\d{3})*(?:,\d{2}))",
            r"([\$€£₹]?\d{3,6})",
        ])

    # If OCR returns a zero-like amount (e.g., 000), choose the largest plausible numeric candidate.
    if total_amount != "Not found":
        normalized = re.sub(r"[^0-9]", "", total_amount)
        if normalized and int(normalized) == 0:
            candidates = re.findall(r"\b\d{2,}(?:[\.,]\d{2})?\b", text)
            if candidates:
                def _score(v):
                    raw = v.replace(",", ".")
                    try:
                        return float(raw)
                    except ValueError:
                        return -1.0
                best = max(candidates, key=_score)
                if _score(best) > 0:
                    total_amount = best

    gst = _first_match(text, [
        r"(?:GST|CGST|SGST|IGST)\s*[:\-]?\s*(\d{1,2}(?:\.\d+)?%)",
    ])

    tax = _first_match(text, [
        r"(?:Tax|GST\s*Amount|Total\s*Tax)\s*[:\-₹$€£\s]*([\d,]+(?:[\.,]\d{1,2})?)",
    ])

    subtotal = _first_match(text, [
        r"(?:Sub\s*Total|Subtotal)\s*[:\-₹$€£\s]*([\d,]+(?:[\.,]\d{1,2})?)",
    ])

    discount = _first_match(text, [
        r"(?:Discount)\s*[:\-₹$€£\s]*([\d,]+(?:[\.,]\d{1,2})?)",
    ])

    payment_method = _first_match(text, [
        r"(?:Payment\s*(?:Mode|Method)?)\s*[:\-]?\s*([A-Za-z ]{2,30})",
        r"\b(UPI|Card|Cash|Net\s*Banking|IMPS|NEFT|RTGS|Wallet)\b",
    ])

    billing_address = _first_match(text, [
        r"(?:Billing\s*Address|Bill\s*To)\s*[:\-]?\s*([^\n]{8,120})",
    ])

    shipping_address = _first_match(text, [
        r"(?:Shipping\s*Address|Ship\s*To)\s*[:\-]?\s*([^\n]{8,120})",
    ])

    items = _extract_items_from_text(text)

    if vendor_name.lower() in {"invoice", "bill", "tax invoice"}:
        vendor_name = "Not found"

    return {
        "vendor_name": vendor_name if vendor_name else "Not found",
        "invoice_number": invoice_number,
        "date": date,
        "gst": gst,
        "tax": tax,
        "subtotal": subtotal,
        "discount": discount,
        "payment_method": payment_method,
        "billing_address": billing_address,
        "shipping_address": shipping_address,
        "items": items,
        "total_amount": total_amount,
    }
