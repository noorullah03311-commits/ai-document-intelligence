import re


def extract_invoice_fields(text):
    fields = {
        "Invoice Number": "Not Found",
        "Date": "Not Found",
        "Company": "Not Found",
        "Total Amount": "Not Found",
        "Email": "Not Found",
        "Phone": "Not Found",
    }
    match = re.search(r"(?:invoice\s*(?:number|no|#)?)[\s:.-]*([A-Z0-9-]+)", text, re.I)
    if match:
        fields["Invoice Number"] = match.group(1)
    match = re.search(r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", text)
    if match:
        fields["Date"] = match.group(1)
    match = re.search(
        r"(?:company\s*name|company)[\s:.-]*(.+?)(?:payment|date|invoice|email|phone|total)",
        text, re.I
    )
    if match:
        fields["Company"] = match.group(1).strip()
    match = re.search(r"(?:total\s*(?:amount)?)[\s:.-]*([A-Z]{2,4})?\s*([\d,]+(?:\.\d+)?)", text, re.I)
    if match:
        fields["Total Amount"] = f"{match.group(1) or ''} {match.group(2)}".strip()
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if match:
        fields["Email"] = match.group(0)
    match = re.search(r"(?:\+?\d[\d\s()-]{7,}\d)", text)
    if match:
        fields["Phone"] = match.group(0).strip()
    return fields


def extract_resume_fields(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    fields = {"Name": lines[0] if lines else "Not Found", "Email": "Not Found", "Phone": "Not Found", "Skills": "Not Found"}
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if match:
        fields["Email"] = match.group(0)
    match = re.search(r"(?:\+?\d[\d\s()-]{7,}\d)", text)
    if match:
        fields["Phone"] = match.group(0).strip()
    match = re.search(r"skills?[\s:.-]*(.*?)(?:experience|education|projects|$)", text, re.I)
    if match:
        fields["Skills"] = match.group(1).strip()
    return fields


def extract_fields(document_type, text):
    if document_type == "Invoice":
        return extract_invoice_fields(text)
    if document_type == "Resume":
        return extract_resume_fields(text)
    return {}
