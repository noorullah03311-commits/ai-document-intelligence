import io
import re
import fitz
import pytesseract
from PIL import Image, ImageOps


def preprocess_image(image):
    image = image.convert("L")
    width, height = image.size
    if width < 1600:
        new_height = int(height * (1600 / width))
        image = image.resize((1600, new_height))
    image = ImageOps.autocontrast(image)
    image = image.point(lambda p: 255 if p > 180 else 0)
    return image


def perform_ocr(image):
    return pytesseract.image_to_string(preprocess_image(image), config="--psm 6")


def extract_pdf_text(file_bytes):
    document = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    try:
        for page in document:
            text += page.get_text() + "\n"
        if len(text.strip()) < 30:
            text = ""
            for page in document:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                image = Image.open(io.BytesIO(pix.tobytes("png")))
                text += perform_ocr(image) + "\n"
    finally:
        document.close()
    return text


def process_document(file_bytes, filename):
    suffix = filename.lower()
    if suffix.endswith(".pdf"):
        text = extract_pdf_text(file_bytes)
    elif suffix.endswith((".jpg", ".jpeg", ".png")):
        image = Image.open(io.BytesIO(file_bytes))
        text = perform_ocr(image)
    else:
        raise ValueError("Unsupported file type.")
    return clean_text(text)


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()
