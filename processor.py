"""PDF text extraction and image OCR with input integrity checks."""
import io
import re

import fitz
import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError


def preprocess_image(image):
    image = image.convert("L")
    width, height = image.size
    if width and width < 1600:
        new_height = max(1, int(height * (1600 / width)))
        image = image.resize((1600, new_height))
    image = ImageOps.autocontrast(image)
    return image.point(lambda pixel: 255 if pixel > 180 else 0)


def perform_ocr(image):
    return pytesseract.image_to_string(preprocess_image(image), config="--psm 6")


def extract_pdf_text(file_bytes):
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError("This PDF is damaged or cannot be opened.") from exc
    text = ""
    try:
        for page in document:
            text += page.get_text() + "\n"
        if len(text.strip()) < 30:
            text = ""
            for page in document:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                with Image.open(io.BytesIO(pix.tobytes("png"))) as image:
                    text += perform_ocr(image) + "\n"
    finally:
        document.close()
    return text


def process_document(file_bytes, filename):
    suffix = str(filename).lower()
    if suffix.endswith(".pdf"):
        text = extract_pdf_text(file_bytes)
    elif suffix.endswith((".jpg", ".jpeg", ".png")):
        try:
            with Image.open(io.BytesIO(file_bytes)) as image:
                image.verify()
            with Image.open(io.BytesIO(file_bytes)) as image:
                text = perform_ocr(image)
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise ValueError("This image is damaged or cannot be opened.") from exc
    else:
        raise ValueError("Unsupported file type. Upload a PDF, JPG, JPEG or PNG file.")
    return clean_text(text)


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()
