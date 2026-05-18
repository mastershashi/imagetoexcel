"""
Full-image OCR engine using EasyOCR.

Scans the entire form image, gets all text with bounding box positions,
then uses row ordering and keyword matching to extract named fields.
No calibration needed.
"""

import logging
import re
import easyocr

logger = logging.getLogger("FormToExcel")

_reader = None


def get_reader(languages=None):
    """Lazy-initialize and cache the EasyOCR reader."""
    global _reader
    if _reader is None:
        langs = languages or ["en"]
        _reader = easyocr.Reader(langs, gpu=False)
    return _reader


def _clean(text):
    """Clean OCR text."""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('|', '').replace('\\', '')
    return text


def _collapse_grid_letters(text):
    """
    Collapse single-character sequences separated by spaces into words.
    E.g. "R A V I K A N T" → "RAVIKANT", but "ROLL NO" stays as-is.
    """
    parts = text.split()
    result = []
    singles = []

    for part in parts:
        if len(part) == 1 and part.isalpha():
            singles.append(part)
        else:
            if singles:
                result.append("".join(singles))
                singles = []
            result.append(part)

    if singles:
        result.append("".join(singles))

    return " ".join(result)


def _merge_into_rows(results, y_threshold=25):
    """
    Group OCR results into rows based on Y proximity.
    Returns list of rows sorted top-to-bottom, each row sorted left-to-right.
    Each row is a list of dicts with x, y, text keys.
    """
    items = []
    for bbox, text, conf in results:
        if conf < 0.05:
            continue
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        items.append({
            "x": min(xs),
            "y": (min(ys) + max(ys)) / 2,
            "text": _clean(text),
        })

    items.sort(key=lambda it: it["y"])

    rows = []
    current_row = []
    last_y = -999

    for item in items:
        if item["y"] - last_y > y_threshold and current_row:
            current_row.sort(key=lambda it: it["x"])
            rows.append(current_row)
            current_row = []
        current_row.append(item)
        last_y = item["y"]

    if current_row:
        current_row.sort(key=lambda it: it["x"])
        rows.append(current_row)

    return rows


def _row_text(row):
    """Join all text in a row."""
    return " ".join(item["text"] for item in row)


def _is_header_row(text):
    """Check if a row is a header/label row (school name, form title, etc.)."""
    t = text.lower()
    header_words = [
        'form', 'capital', 'letter', 'only', 'school', 'english',
        'vidya', 'mandir', 'ranchi', 'ratu', 'khatitanr', 'photo no',
        'photo mo',
    ]
    matches = sum(1 for w in header_words if w in t)
    return matches >= 2


def _extract_after_keyword(text, pattern):
    """Extract text appearing after a keyword pattern."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        after = text[match.end():].strip()
        after = re.sub(r'^[:\-.\s;,]+', '', after).strip()
        return after
    return ""


def _extract_roll_no(text):
    """Extract roll number from a row containing SEC/ROLL NO/HOUSE."""
    match = re.search(r'ROLL\s*(?:NO|N0|MO)[:\-.\s]*(.+?)(?:(?:HOUSE|IQUSE|$))',
                      text, re.IGNORECASE)
    if match:
        val = match.group(1).strip()
        val = re.sub(r'[:\-.\s;,]+$', '', val)
        return val

    match = re.search(r'(?:NO|N0)[:\-.\s]*(\w+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _extract_section(text):
    """Extract section from a row."""
    match = re.search(r'\bSEC[:\-.\s]*(\w*)', text, re.IGNORECASE)
    if match:
        val = match.group(1).strip()
        if val and not re.search(r'roll|no', val, re.IGNORECASE):
            return val
    return ""


def _extract_dob(text):
    """Extract date of birth from text containing numbers and 'Date of Birth' label."""
    match = re.search(r'd[ae]te\s*of\s*birth', text, re.IGNORECASE)
    if match:
        before = text[:match.start()]
        after = text[match.end():]
        before_digits = re.findall(r'\d+', before)
        after_digits = re.findall(r'\d+', after)
        digits = before_digits if len(before_digits) >= len(after_digits) else after_digits
    else:
        digits = re.findall(r'\d+', text)

    if len(digits) >= 3:
        return "/".join(digits[:4])
    return ""


def ocr_full_image(image, reader=None):
    """
    Run OCR on the full form image and extract structured fields.
    Uses row ordering: header, student name, sec/roll/house, father, mother, address, dob.

    Args:
        image: OpenCV BGR image (numpy array).
        reader: EasyOCR reader instance (optional).

    Returns:
        Dict of field_name -> extracted text.
    """
    if reader is None:
        reader = get_reader()

    logger.info("OCR input image shape: %s, dtype: %s", image.shape, image.dtype)

    results = reader.readtext(image, detail=1, paragraph=False)

    logger.info("EasyOCR returned %d raw text blocks", len(results))
    for i, (bbox, text, conf) in enumerate(results):
        logger.debug("  Block %d: conf=%.2f text='%s' bbox=%s", i, conf, text, bbox)

    empty = {
        "student_name": "", "father_name": "", "mother_name": "",
        "class": "", "roll_no": "", "section": "", "address": "",
        "date_of_birth": "", "photo_no": "",
    }

    if not results:
        logger.warning("EasyOCR returned NO results at all")
        return empty

    rows = _merge_into_rows(results)
    logger.info("Merged into %d rows", len(rows))
    for i, row in enumerate(rows):
        logger.info("  Row %d: '%s'", i, _row_text(row))

    if not rows:
        logger.warning("No rows after merging")
        return empty

    data_rows = []
    sec_roll_row = None

    for row in rows:
        text = _row_text(row)

        if _is_header_row(text):
            logger.info("    -> SKIPPED (header row)")
            continue

        t_lower = text.lower()
        if ('sec' in t_lower and 'roll' in t_lower) or 'roll no' in t_lower:
            sec_roll_row = text
            logger.info("    -> SEC/ROLL row: '%s'", text)
            continue

        if re.search(r'd[ae]te\s*of\s*birth|d\.?o\.?b', t_lower):
            data_rows.append(("dob", text))
            logger.info("    -> DOB row: '%s'", text)
            continue

        data_rows.append(("data", text))
        logger.info("    -> DATA row: '%s'", text)

    extracted = dict(empty)

    if sec_roll_row:
        extracted["roll_no"] = _extract_roll_no(sec_roll_row)
        extracted["section"] = _extract_section(sec_roll_row)

    name_rows = []
    dob_row = None

    for rtype, text in data_rows:
        if rtype == "dob":
            dob_row = text
            continue

        alpha_only = re.sub(r'[^a-zA-Z]', '', text)
        if len(alpha_only) < 2:
            continue

        cleaned = text
        cleaned = re.sub(r'^.*?(?:ENT|DENT|udent)[:\-.\s;]*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^[:\-.\s;,]+', '', cleaned).strip()
        if cleaned:
            name_rows.append(cleaned)

    if len(name_rows) >= 1:
        extracted["student_name"] = _collapse_grid_letters(name_rows[0])
    if len(name_rows) >= 2:
        extracted["father_name"] = _collapse_grid_letters(name_rows[1])
    if len(name_rows) >= 3:
        extracted["mother_name"] = _collapse_grid_letters(name_rows[2])
    if len(name_rows) >= 4:
        extracted["address"] = _collapse_grid_letters(name_rows[3])
    if len(name_rows) >= 5:
        remaining = _collapse_grid_letters(" ".join(name_rows[4:]))
        if not extracted["address"]:
            extracted["address"] = remaining

    if dob_row:
        extracted["date_of_birth"] = _extract_dob(dob_row)

    for key in extracted:
        val = extracted[key]
        val = re.sub(r'^[:\-.\s;,]+', '', val).strip()
        val = re.sub(r'[:\-.\s;,]+$', '', val).strip()
        if key in ("student_name", "father_name", "mother_name", "address"):
            val = re.sub(r'[^a-zA-Z\s]', '', val).strip()
            val = re.sub(r'\s+', ' ', val)
        extracted[key] = val.upper() if val else ""

    logger.info("Final extracted fields:")
    for k, v in extracted.items():
        logger.info("  %s: '%s'", k, v)

    return extracted


def ocr_all_fields(field_images, reader=None):
    """Legacy wrapper kept for backward compatibility."""
    if reader is None:
        reader = get_reader()
    results = {}
    for field_name, img in field_images.items():
        text_results = reader.readtext(img, detail=0, paragraph=True)
        results[field_name] = _clean(" ".join(text_results)) if text_results else ""
    return results
