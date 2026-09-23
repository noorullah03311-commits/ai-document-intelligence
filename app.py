import streamlit as st
import fitz
import pytesseract
import re
import io
import os
import hashlib
from datetime import datetime

from PIL import Image, ImageOps

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

from storage_manager import get_storage_path

from database import (
    create_database,
    insert_document,
    document_hash_exists,
    search_documents,
    get_filtered_documents,
    get_all_documents,
    get_document_by_id
)


# =========================================================
# DATABASE
# =========================================================

create_database()


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Document Intelligence & Workflow Platform")

st.write(
    "Upload, process, store and search your documents."
)


# =========================================================
# TASK 7: PROCESSING STATUS
# =========================================================

def display_status(status):

    if status == "Processed":

        st.success("✅ Processing Status: Processed")

    elif status == "Needs Review":

        st.warning("⚠️ Processing Status: Needs Review")

    elif status == "Failed":

        st.error("❌ Processing Status: Failed")

    else:

        st.info(f"Processing Status: {status}")


# =========================================================
# SHA-256 HASH
# =========================================================

def calculate_file_hash(file_bytes):

    return hashlib.sha256(file_bytes).hexdigest()


# =========================================================
# OCR
# =========================================================

def preprocess_image(image):

    image = image.convert("L")

    width, height = image.size

    if width < 1600:

        new_height = int(
            height * (1600 / width)
        )

        image = image.resize(
            (1600, new_height)
        )

    image = ImageOps.autocontrast(image)

    image = image.point(
        lambda p: 255 if p > 180 else 0
    )

    return image


def perform_ocr(image):

    processed_image = preprocess_image(image)

    text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6"
    )

    return text


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_pdf_text(file_bytes):

    pdf_document = fitz.open(
        stream=file_bytes,
        filetype="pdf"
    )

    text = ""

    for page in pdf_document:

        page_text = page.get_text()

        if page_text:

            text += page_text + "\n"

    # OCR fallback for scanned PDFs
    if len(text.strip()) < 30:

        text = ""

        for page in pdf_document:

            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image = Image.open(
                io.BytesIO(
                    pix.tobytes("png")
                )
            )

            text += perform_ocr(image) + "\n"

    pdf_document.close()

    return text


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# DOCUMENT CLASSIFICATION
# =========================================================

def classify_document(text):

    dataset_path = "dataset/week3_dataset"

    categories = [
        "Invoice",
        "Other",
        "Resume"
    ]

    training_texts = []
    training_labels = []

    if os.path.exists(dataset_path):

        for category in categories:

            category_path = os.path.join(
                dataset_path,
                category
            )

            if not os.path.exists(category_path):

                continue

            for filename in os.listdir(
                category_path
            ):

                file_path = os.path.join(
                    category_path,
                    filename
                )

                if filename.lower().endswith(".txt"):

                    try:

                        with open(
                            file_path,
                            "r",
                            encoding="utf-8"
                        ) as file:

                            training_texts.append(
                                file.read()
                            )

                            training_labels.append(
                                category
                            )

                    except Exception:

                        pass

    if len(training_texts) < 2:

        return "Other"

    vectorizer = TfidfVectorizer()

    X = vectorizer.fit_transform(
        training_texts
    )

    model = MultinomialNB()

    model.fit(
        X,
        training_labels
    )

    document_vector = vectorizer.transform(
        [text]
    )

    prediction = model.predict(
        document_vector
    )[0]

    return prediction


# =========================================================
# INVOICE EXTRACTION
# =========================================================

def extract_invoice_fields(text):

    invoice_number = "Not Found"
    date = "Not Found"
    company = "Not Found"
    total_amount = "Not Found"
    email = "Not Found"
    phone = "Not Found"

    match = re.search(
        r"(?:invoice\s*(?:number|no|#)?)[\s:.-]*([A-Z0-9-]+)",
        text,
        re.IGNORECASE
    )

    if match:

        invoice_number = match.group(1)

    match = re.search(
        r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
        text
    )

    if match:

        date = match.group(1)

    match = re.search(
        r"(?:company\s*name|company)[\s:.-]*(.+?)(?:payment|date|invoice|email|phone|total)",
        text,
        re.IGNORECASE
    )

    if match:

        company = match.group(1).strip()

    match = re.search(
        r"(?:total\s*(?:amount)?)[\s:.-]*([A-Z]{2,4})?\s*([\d,]+(?:\.\d+)?)",
        text,
        re.IGNORECASE
    )

    if match:

        currency = match.group(1) or ""

        amount = match.group(2)

        total_amount = f"{currency} {amount}".strip()

    match = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text
    )

    if match:

        email = match.group(0)

    match = re.search(
        r"(?:\+?\d[\d\s()-]{7,}\d)",
        text
    )

    if match:

        phone = match.group(0).strip()

    return {
        "Invoice Number": invoice_number,
        "Date": date,
        "Company": company,
        "Total Amount": total_amount,
        "Email": email,
        "Phone": phone
    }


# =========================================================
# RESUME EXTRACTION
# =========================================================

def extract_resume_fields(text):

    name = "Not Found"
    email = "Not Found"
    phone = "Not Found"
    skills = "Not Found"

    lines = [
        line.strip()
        for line in text.split("\n")
        if line.strip()
    ]

    if lines:

        name = lines[0]

    match = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text
    )

    if match:

        email = match.group(0)

    match = re.search(
        r"(?:\+?\d[\d\s()-]{7,}\d)",
        text
    )

    if match:

        phone = match.group(0).strip()

    match = re.search(
        r"skills?[\s:.-]*(.*?)(?:experience|education|projects|$)",
        text,
        re.IGNORECASE
    )

    if match:

        skills = match.group(1).strip()

    return {
        "Name": name,
        "Email": email,
        "Phone": phone,
        "Skills": skills
    }


# =========================================================
# SEARCH
# =========================================================

st.header("🔎 Search Documents")

search_text = st.text_input(
    "Search by filename, company, invoice number, document type or text"
)

if search_text:

    results = search_documents(
        search_text
    )

    if results:

        st.success(
            f"{len(results)} document(s) found."
        )

        for document in results:

            st.write("---")

            st.write(
                f"**ID:** {document[0]}"
            )

            st.write(
                f"**Filename:** {document[1]}"
            )

            st.write(
                f"**Type:** {document[3]}"
            )

            st.write(
                f"**Company:** {document[5] or 'Not Available'}"
            )

            st.write(
                f"**Invoice Number:** {document[6] or 'Not Available'}"
            )

            st.write(
                f"**Upload Date:** {document[4]}"
            )

            st.write(
                f"**Status:** {document[11]}"
            )

            st.write(
                f"**Preview:** {document[9]}"
            )

    else:

        st.warning(
            "No matching documents found."
        )


# =========================================================
# FILTERS AND SORTING
# =========================================================

st.header("📂 Filters & Sorting")

if st.button("🧹 Clear Filters"):

    st.session_state["type_filter"] = "All"
    st.session_state["status_filter"] = "All"
    st.session_state["date_filter"] = None
    st.session_state["sort_filter"] = "Newest"

    st.rerun()


col1, col2 = st.columns(2)


with col1:

    document_type_filter = st.selectbox(
        "Filter by Document Type",
        ["All", "Invoice", "Resume", "Other"],
        key="type_filter"
    )


with col2:

    status_filter = st.selectbox(
        "Filter by Processing Status",
        ["All", "Processed", "Needs Review", "Failed"],
        key="status_filter"
    )


upload_date_filter = st.date_input(
    "Filter by Upload Date (optional)",
    value=None,
    key="date_filter"
)


sort_filter = st.selectbox(
    "Sort Documents",
    ["Newest", "Oldest"],
    key="sort_filter"
)


filtered_documents = get_filtered_documents(
    document_type=document_type_filter,
    status=status_filter,
    upload_date=upload_date_filter,
    sort_order=sort_filter
)


st.subheader("📑 Filtered Documents")


if filtered_documents:

    st.success(
        f"{len(filtered_documents)} document(s) found."
    )

    for document in filtered_documents:

        st.write("---")

        st.write(
            f"**ID:** {document[0]}"
        )

        st.write(
            f"**Original Filename:** {document[1]}"
        )

        st.write(
            f"**Stored Filename:** {document[2]}"
        )

        st.write(
            f"**Document Type:** {document[3]}"
        )

        st.write(
            f"**Upload Date:** {document[4]}"
        )

        st.write(
            f"**Company:** {document[5] or 'Not Available'}"
        )

        st.write(
            f"**Invoice Number:** {document[6] or 'Not Available'}"
        )

        st.write(
            f"**Total Amount:** {document[7] or 'Not Available'}"
        )

        st.write(
            f"**File Location:** {document[8]}"
        )

        display_status(
            document[11]
        )

else:

    st.info(
        "No documents match these filters."
    )


# =========================================================
# DOCUMENT DETAIL VIEW
# =========================================================

st.header("📋 Document Detail View")

all_documents = get_all_documents()


if all_documents:

    document_options = {
        f"{document[0]} - {document[1]}": document[0]
        for document in all_documents
    }

    selected_document_label = st.selectbox(
        "Select a document to view details",
        list(document_options.keys())
    )

    selected_document_id = document_options[
        selected_document_label
    ]

    selected_document = get_document_by_id(
        selected_document_id
    )

    if selected_document:

        st.subheader("📄 Document Information")

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Document ID:** {selected_document[0]}"
            )

            st.write(
                f"**Original Filename:** {selected_document[1]}"
            )

            st.write(
                f"**Stored Filename:** {selected_document[2]}"
            )

            st.write(
                f"**Document Type:** {selected_document[3]}"
            )

            st.write(
                f"**Upload Date:** {selected_document[4]}"
            )

        with col2:

            st.write(
                f"**Company:** {selected_document[5] or 'Not Available'}"
            )

            st.write(
                f"**Invoice Number:** {selected_document[6] or 'Not Available'}"
            )

            st.write(
                f"**Total Amount:** {selected_document[7] or 'Not Available'}"
            )

            display_status(
                selected_document[11]
            )

            st.write(
                f"**File Location:** {selected_document[8]}"
            )

        st.subheader("📝 Text Preview")

        if selected_document[9]:

            st.text_area(
                "Stored Text Preview",
                selected_document[9],
                height=200,
                disabled=True
            )

        else:

            st.info(
                "No text preview is available."
            )

        st.subheader("📂 File")

        file_path = selected_document[8]

        if os.path.exists(file_path):

            try:

                with open(
                    file_path,
                    "rb"
                ) as file:

                    file_data = file.read()

                st.success(
                    "Saved file is available."
                )

                st.download_button(
                    label="⬇️ Download Document",
                    data=file_data,
                    file_name=selected_document[1],
                    mime="application/octet-stream"
                )

            except Exception:

                st.error(
                    "The saved document could not be opened."
                )

        else:

            st.warning(
                "The saved file could not be found at the stored location."
            )

else:

    st.info(
        "No documents are available. Upload a document first."
    )


# =========================================================
# UPLOAD NEW DOCUMENT
# =========================================================

st.header("📤 Upload New Document")

uploaded_file = st.file_uploader(
    "Upload a document",
    type=[
        "pdf",
        "jpg",
        "jpeg",
        "png"
    ]
)


# =========================================================
# PROCESS FILE
# =========================================================

if uploaded_file is not None:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    file_bytes = uploaded_file.getvalue()

    # =====================================================
    # SHA-256 HASH
    # =====================================================

    file_hash = calculate_file_hash(
        file_bytes
    )

    # =====================================================
    # DUPLICATE CHECK
    # =====================================================

    existing_document = document_hash_exists(
        file_hash
    )

    if existing_document:

        st.warning(
            "⚠️ Duplicate document detected!"
        )

        st.write(
            f"**Original filename:** {existing_document[1]}"
        )

        st.write(
            f"**Document type:** {existing_document[3]}"
        )

        st.write(
            f"**Upload date:** {existing_document[4]}"
        )

        display_status(
            existing_document[11]
        )

        st.write(
            f"**File location:** {existing_document[8]}"
        )

        st.info(
            "This file already exists. A new copy was not created."
        )

        st.stop()

    # =====================================================
    # VARIABLES
    # =====================================================

    extracted_text = ""

    company = ""
    invoice_number = ""
    total_amount = ""

    predicted_type = "Other"

    status = "Processed"

    # =====================================================
    # STORAGE FOLDER
    # =====================================================

    storage_type = "other"

    if "invoice" in uploaded_file.name.lower():

        storage_type = "invoice"

    elif "resume" in uploaded_file.name.lower():

        storage_type = "resume"

    # =====================================================
    # SAVE FILE
    # =====================================================

    try:

        storage_path = get_storage_path(
            storage_type,
            uploaded_file.name
        )

        with open(
            storage_path,
            "wb"
        ) as file:

            file.write(file_bytes)

        st.success(
            f"File saved: {storage_path}"
        )

    except Exception:

        st.error(
            "The file could not be saved."
        )

        st.stop()

    # =====================================================
    # EXTRACT TEXT
    # =====================================================

    try:

        if uploaded_file.name.lower().endswith(
            ".pdf"
        ):

            extracted_text = extract_pdf_text(
                file_bytes
            )

        else:

            image = Image.open(
                io.BytesIO(file_bytes)
            )

            extracted_text = perform_ocr(
                image
            )

        extracted_text = clean_text(
            extracted_text
        )

        if not extracted_text:

            status = "Failed"

            st.error(
                "❌ No readable text could be extracted."
            )

        else:

            st.success(
                "Text extraction completed successfully."
            )

    except Exception:

        status = "Failed"

        st.error(
            "❌ The document could not be processed."
        )

    # =====================================================
    # CLASSIFICATION
    # =====================================================

    if extracted_text and status != "Failed":

        try:

            predicted_type = classify_document(
                extracted_text
            )

            st.subheader(
                "📂 Document Classification"
            )

            st.write(
                f"Document Type: **{predicted_type}**"
            )

        except Exception:

            predicted_type = "Other"

            status = "Needs Review"

            st.warning(
                "⚠️ Classification could not be completed. Document needs review."
            )

    # =====================================================
    # EXTRACTED TEXT
    # =====================================================

    if extracted_text:

        st.subheader(
            "📝 Extracted Text"
        )

        st.text_area(
            "OCR / Document Text",
            extracted_text,
            height=250
        )

    # =====================================================
    # INVOICE PROCESSING
    # =====================================================

    if (
        extracted_text
        and predicted_type == "Invoice"
        and status != "Failed"
    ):

        fields = extract_invoice_fields(
            extracted_text
        )

        st.subheader(
            "🧾 Invoice Information"
        )

        for key, value in fields.items():
            st.write(
                f"**{key}:** {value}"
            )

        company = fields["Company"]

        invoice_number = fields["Invoice Number"]

        total_amount = fields["Total Amount"]

        # Task 7:
        # Missing important invoice information
        # means the document needs manual review.

        if (
            company == "Not Found"
            or invoice_number == "Not Found"
            or total_amount == "Not Found"
        ):

            status = "Needs Review"

            st.warning(
                "⚠️ Important invoice information is missing. "
                "This document needs review."
            )

    # =====================================================
    # RESUME PROCESSING
    # =====================================================

    elif (
        extracted_text
        and predicted_type == "Resume"
        and status != "Failed"
    ):

        fields = extract_resume_fields(
            extracted_text
        )

        st.subheader(
            "👤 Resume Information"
        )

        for key, value in fields.items():

            st.write(
                f"**{key}:** {value}"
            )

        # Task 7:
        # Missing important resume fields
        # means the document needs review.

        if (
            fields["Name"] == "Not Found"
            or fields["Email"] == "Not Found"
            or fields["Phone"] == "Not Found"
        ):

            status = "Needs Review"

            st.warning(
                "⚠️ Important resume information is missing. "
                "This document needs review."
            )

    # =====================================================
    # OTHER DOCUMENT
    # =====================================================

    elif (
        extracted_text
        and predicted_type == "Other"
        and status != "Failed"
    ):

        st.info(
            "This document is classified as Other."
        )

    # =====================================================
    # FINAL PROCESSING STATUS
    # =====================================================

    st.subheader(
        "📊 Processing Result"
    )

    display_status(
        status
    )

    # =====================================================
    # SAVE METADATA
    # =====================================================

    try:

        upload_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        stored_filename = storage_path.name

        text_preview = extracted_text[:500]

        insert_document(
            original_filename=uploaded_file.name,
            stored_filename=stored_filename,
            document_type=predicted_type,
            upload_date=upload_date,
            company=company,
            invoice_number=invoice_number,
            total_amount=total_amount,
            file_path=str(storage_path),
            text_preview=text_preview,
            file_hash=file_hash,
            status=status
        )

        st.success(
            "✅ Document metadata saved to SQLite database."
        )

        if status == "Processed":

            st.success(
                "Document processing completed successfully."
            )

        elif status == "Needs Review":

            st.warning(
                "Document was processed, but some information "
                "needs manual review."
            )

        elif status == "Failed":

            st.error(
                "Document processing failed. "
                "The failure status has been saved."
            )

    except Exception:

        st.error(
            "The document was processed, but its metadata could not be saved."
        )