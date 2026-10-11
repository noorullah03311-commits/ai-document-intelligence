"""Upload checks performed before OCR or database writes."""
from pathlib import Path

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def validate_upload(filename, file_bytes, max_size=MAX_FILE_SIZE_BYTES):
    """Return None for a supported upload or a human-readable error string."""
    if not filename or not str(filename).strip():
        return "The uploaded file has no filename."
    extension = Path(str(filename)).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return "Unsupported file type. Upload a PDF, JPG, JPEG or PNG file."
    if not isinstance(file_bytes, (bytes, bytearray)) or not file_bytes:
        return "The file is empty or unreadable."
    if len(file_bytes) > max_size:
        return "File is larger than the 10 MB upload limit."

    data = bytes(file_bytes)
    if extension == ".pdf":
        # PDF headers are normally at byte zero; allow a short prefix for valid PDFs.
        if b"%PDF-" not in data[:1024]:
            return "The file does not appear to be a valid PDF."
    elif extension in {".jpg", ".jpeg"}:
        if not (data.startswith(b"\xff\xd8\xff") and data.rstrip().endswith(b"\xff\xd9")):
            return "The file does not appear to be a valid JPEG image."
    elif extension == ".png":
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "The file does not appear to be a valid PNG image."
    return None
