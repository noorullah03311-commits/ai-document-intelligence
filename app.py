import streamlit as st
import pymupdf
import pytesseract
import re
import io
import os

from PIL import Image, ImageOps
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

from storage_manager import get_storage_path


# ==============================
# PAGE SETTINGS
# ==============================

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Document Intelligence")
st.write("Upload a PDF or image to analyze the document.")


# ==============================
# TEXT CLEANING
# ==============================

def clean_text(text):
    text = text.replace("\x00", " ")

    text = re.sub(
        r"(\w)-\s*\n\s*(\w)",
        r"\1\2",
        text
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n",
        text
    )

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines).strip()


# ==============================
# OCR PREPROCESSING
# ==============================

def preprocess_image(image):

    image = image.convert("L")

    width, height = image.size

    if width < 1600:
        scale = 1600 / width

        image = image.resize(
            (int(width * scale), int(height * scale))
        )

    image = ImageOps.autocontrast(image)

    image = image.point(
        lambda pixel: 0 if pixel < 180 else 255
    )

    return image


def run_ocr(image):

    processed_image = preprocess_image(image)

    text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6"
    )

    return clean_text(text)


# ==============================
# PDF TEXT EXTRACTION
# ==============================

def extract_pdf_text(pdf_bytes):

    extracted_text = ""

    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    for page in document:
        extracted_text += page.get_text() + "\n"

    document.close()

    extracted_text = clean_text(extracted_text)

    if len(extracted_text) < 30:

        extracted_text = ""

        document = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        for page in document:

            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(2, 2),
                alpha=False
            )

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            extracted_text += run_ocr(image) + "\n"

        document.close()

        extracted_text = clean_text(extracted_text)

    return extracted_text


# ==============================
# RULE-BASED CLASSIFICATION
# ==============================

def rule_based_classification(text):

    text_lower = text.lower()

    invoice_keywords = [
        "invoice",
        "invoice number",
        "bill to",
        "total amount",
        "subtotal",
        "tax",
        "grand total"
    ]

    resume_keywords = [
        "resume",
        "curriculum vitae",
        "education",
        "experience",
        "skills",
        "projects"
    ]

    invoice_score = sum(
        keyword in text_lower
        for keyword in invoice_keywords
    )

    resume_score = sum(
        keyword in text_lower
        for keyword in resume_keywords
    )

    if invoice_score > resume_score and invoice_score >= 2:
        return "Invoice"

    elif resume_score > invoice_score and resume_score >= 2:
        return "Resume"

    return "Other"


# ==============================
# TRAIN ML MODEL
# ==============================

@st.cache_resource
def train_ml_model():

    dataset_path = "dataset/week3_dataset"

    categories = [
        "Invoice",
        "Other",
        "Resume"
    ]

    texts = []
    labels = []

    if not os.path.exists(dataset_path):
        return None, None

    for category in categories:

        folder = os.path.join(
            dataset_path,
            category
        )

        if not os.path.exists(folder):
            continue

        for filename in os.listdir(folder):

            if not filename.lower().endswith(".pdf"):
                continue

            filepath = os.path.join(
                folder,
                filename
            )

            try:

                with open(filepath, "rb") as file:
                    pdf_bytes = file.read()

                text = extract_pdf_text(
                    pdf_bytes
                )

                if len(text) > 20:

                    texts.append(text)
                    labels.append(category)

            except Exception:
                pass

    if len(texts) < 6:
        return None, None

    vectorizer = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 2)
    )

    X = vectorizer.fit_transform(texts)

    model = MultinomialNB()

    model.fit(
        X,
        labels
    )

    return model, vectorizer


# ==============================
# INVOICE EXTRACTION
# ==============================

def extract_invoice_fields(text):

    fields = {}

    invoice_number = re.search(
        r"(?:invoice\s*(?:number|no\.?|#)|inv(?:oice)?\s*#?)"
        r"\s*[:\-]?\s*([A-Za-z0-9\-]+)",
        text,
        re.IGNORECASE
    )

    fields["Invoice Number"] = (
        invoice_number.group(1).strip()
        if invoice_number
        else "Not Found"
    )

    date = re.search(
        r"\b(?:date|invoice date)\s*[:\-]?\s*"
        r"(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})",
        text,
        re.IGNORECASE
    )

    fields["Date"] = (
        date.group(1).strip()
        if date
        else "Not Found"
    )

    company = re.search(
        r"company\s*name\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )

    if company:
        fields["Company Name"] = company.group(1).strip()

    else:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        company_name = "Not Found"

        for line in lines[:5]:

            lower_line = line.lower()

            if (
                "invoice" not in lower_line
                and "date" not in lower_line
                and "email" not in lower_line
                and "phone" not in lower_line
            ):
                company_name = line
                break

        fields["Company Name"] = company_name

    total = re.search(
        r"(?:total\s*amount|grand\s*total|total)"
        r"\s*[:\-]?\s*([^\n]+)",
        text,
        re.IGNORECASE
    )

    fields["Total Amount"] = (
        total.group(1).strip()
        if total
        else "Not Found"
    )

    email = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text
    )

    fields["Email"] = (
        email.group(0).strip()
        if email
        else "Not Found"
    )

    phone = re.search(
        r"\+?\d[\d\s\-]{8,}\d",
        text
    )

    fields["Phone"] = (
        phone.group(0).strip()
        if phone
        else "Not Found"
    )

    return fields


# ==============================
# RESUME EXTRACTION
# ==============================

def extract_resume_fields(text):

    fields = {}

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    name = None

    for i, line in enumerate(lines):

        if line.upper() in [
            "RESUME",
            "CURRICULUM VITAE",
            "CV"
        ]:

            if i + 1 < len(lines):
                name = lines[i + 1]

            break

    if not name and lines:
        name = lines[0]

    fields["Name"] = (
        name
        if name
        else "Not Found"
    )

    email = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text
    )

    fields["Email"] = (
        email.group(0).strip()
        if email
        else "Not Found"
    )

    phone = re.search(
        r"\+?\d[\d\s\-]{8,}\d",
        text
    )

    fields["Phone"] = (
        phone.group(0).strip()
        if phone
        else "Not Found"
    )

    skills = re.search(
        r"SKILLS\s*(.*?)"
        r"(?=PROJECTS|EXPERIENCE|EDUCATION|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if skills:

        skills_text = skills.group(1).strip()

        skill_lines = [
            line.strip()
            for line in skills_text.splitlines()
            if line.strip()
        ]

        fields["Skills"] = ", ".join(
            skill_lines
        )

    else:
        fields["Skills"] = "Not Found"

    return fields


# ==============================
# UPLOAD
# ==============================

uploaded_file = st.file_uploader(
    "Choose a document",
    type=[
        "pdf",
        "jpg",
        "jpeg",
        "png"
    ]
)


# ==============================
# PROCESS DOCUMENT
# ==============================

if uploaded_file is not None:

    st.success(
        f"File uploaded: {uploaded_file.name}"
    )

    st.write("### File Information")

    st.write(
        f"**Filename:** {uploaded_file.name}"
    )

    st.write(
        f"**File type:** {uploaded_file.type}"
    )

    st.write(
        f"**File size:** "
        f"{uploaded_file.size / 1024:.2f} KB"
    )

    extracted_text = ""

    # ==============================
    # SAVE UPLOADED FILE
    # ==============================

    document_type = "other"

    if "invoice" in uploaded_file.name.lower():
        document_type = "invoice"

    elif "resume" in uploaded_file.name.lower():
        document_type = "resume"

    storage_path = get_storage_path(
        document_type,
        uploaded_file.name
    )

    with open(storage_path, "wb") as file:
        file.write(
            uploaded_file.getbuffer()
        )

    st.success(
        f"File saved: {storage_path}"
    )

    # ==============================
    # PDF
    # ==============================

    if uploaded_file.type == "application/pdf":

        pdf_bytes = uploaded_file.read()

        extracted_text = extract_pdf_text(
            pdf_bytes
        )

    # ==============================
    # IMAGE
    # ==============================

    else:

        image = Image.open(
            uploaded_file
        )

        st.image(
            image,
            caption="Uploaded document",
            use_container_width=True
        )

        st.info(
            "Running improved OCR..."
        )

        extracted_text = run_ocr(
            image
        )

    # ==============================
    # RESULT
    # ==============================

    if extracted_text:

        st.write("### Cleaned Text")

        st.text_area(
            "Document text",
            extracted_text,
            height=300
        )

        # ML model
        model, vectorizer = train_ml_model()

        document_type = None
        confidence = None

        if model is not None:

            try:

                X_uploaded = vectorizer.transform(
                    [extracted_text]
                )

                document_type = model.predict(
                    X_uploaded
                )[0]

                probabilities = model.predict_proba(
                    X_uploaded
                )[0]

                confidence = max(
                    probabilities
                ) * 100

            except Exception:
                document_type = None

        # Rule-based fallback
        if document_type is None:

            document_type = rule_based_classification(
                extracted_text
            )

        st.write("### Document Type")

        if document_type == "Invoice":
            st.success("🧾 Invoice")

        elif document_type == "Resume":
            st.success("📄 Resume")

        else:
            st.info("❓ Other")

        # Confidence
        if confidence is not None:

            st.write(
                f"**Model Confidence:** "
                f"{confidence:.2f}%"
            )

            if confidence < 60:

                st.warning(
                    "Low confidence classification. "
                    "Please verify the result."
                )

        # ==============================
        # FIELD EXTRACTION
        # ==============================

        if document_type == "Invoice":

            fields = extract_invoice_fields(
                extracted_text
            )

            st.write(
                "### Extracted Invoice Fields"
            )

            for field, value in fields.items():

                st.write(
                    f"**{field}:** {value}"
                )

        elif document_type == "Resume":

            fields = extract_resume_fields(
                extracted_text
            )

            st.write(
                "### Extracted Resume Fields"
            )

            for field, value in fields.items():

                st.write(
                    f"**{field}:** {value}"
                )

        else:

            st.info(
                "No specific fields are available "
                "for this document type."
            )

    else:

        st.warning(
            "No text could be extracted from "
            "this document."
        )