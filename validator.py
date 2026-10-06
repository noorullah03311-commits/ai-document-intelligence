import re
from datetime import datetime


NOT_FOUND_VALUES = {"", "Not Found", "Not found", "N/A", "None", None}


def is_missing(value):
    return value in NOT_FOUND_VALUES or (isinstance(value, str) and not value.strip())


def valid_email(value):
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(value).strip()))


def valid_phone(value):
    digits = re.sub(r"\D", "", str(value))
    return 8 <= len(digits) <= 15


def valid_date(value):
    if is_missing(value):
        return False
    value = str(value).strip()
    formats = ("%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y")
    for fmt in formats:
        try:
            datetime.strptime(value, fmt)
            return True
        except ValueError:
            pass
    return False


def valid_amount(value):
    if is_missing(value):
        return False
    cleaned = re.sub(r"[^\d.]", "", str(value))
    try:
        return float(cleaned) >= 0
    except ValueError:
        return False


def validate_document(document_type, fields):
    errors, missing = [], []

    if document_type == "Invoice":
        required = ("Invoice Number", "Date", "Company", "Total Amount")
        for field in required:
            if is_missing(fields.get(field)):
                missing.append(field)
                errors.append(f"{field} is missing")
        if not is_missing(fields.get("Date")) and not valid_date(fields.get("Date")):
            errors.append("Date has an invalid format")
        if not is_missing(fields.get("Total Amount")) and not valid_amount(fields.get("Total Amount")):
            errors.append("Total Amount is not a valid numeric amount")
        if not is_missing(fields.get("Email")) and not valid_email(fields.get("Email")):
            errors.append("Email has an invalid format")
        if not is_missing(fields.get("Phone")) and not valid_phone(fields.get("Phone")):
            errors.append("Phone has an invalid format")

    elif document_type == "Resume":
        for field in ("Name", "Email", "Skills"):
            if is_missing(fields.get(field)):
                missing.append(field)
                errors.append(f"{field} is missing")
        if not is_missing(fields.get("Email")) and not valid_email(fields.get("Email")):
            errors.append("Email has an invalid format")
        if not is_missing(fields.get("Phone")) and not valid_phone(fields.get("Phone")):
            errors.append("Phone has an invalid format")

    else:
        # "Other" has no required business fields in the Week 5 specification.
        pass

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "missing_fields": missing,
    }
