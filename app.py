import streamlit as st
import fitz
import pytesseract
from PIL import Image
import io
import re


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="📄",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("📄 AI Document Intelligence")
st.write("Upload a PDF or image to analyze the document.")


# =========================================================
# FILE UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Choose a document",
    type=["pdf", "jpg", "jpeg", "png"]
)


# =========================================================
# DOCUMENT CLASSIFICATION
# =========================================================

def classify_document(text):

    text_lower = text.lower()

    invoice_keywords = [
        "invoice",
        "invoice number",
        "bill to",
        "total amount",
        "subtotal",
        "tax"
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

    else:
        return "Other"


# =========================================================
# INVOICE FIELD EXTRACTION
# =========================================================

def extract_invoice_fields(text):

    fields = {}

    invoice_number = re.search(
        r"Invoice Number\s*[:\-]?\s*([A-Za-z0-9\-]+)",
        text,
        re.IGNORECASE
    )

    date = re.search(
        r"Date\s*[:\-]?\s*(\d{2}-\d{2}-\d{4})",
        text,
        re.IGNORECASE
    )

    company = re.search(
        r"Company Name\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )

    payment_due = re.search(
        r"Payment Due\s*[:\-]?\s*(\d{2}-\d{2}-\d{4})",
        text,
        re.IGNORECASE
    )

    email = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text
    )

    phone = re.search(
        r"\+?\d[\d\s\-]{8,}\d",
        text
    )

    total = re.search(
        r"Total Amount\s*[:\-]?\s*(.+)",
        text,
        re.IGNORECASE
    )

    if invoice_number:
        fields["Invoice Number"] = invoice_number.group(1).strip()

    if date:
        fields["Date"] = date.group(1).strip()

    if company:
        fields["Company Name"] = company.group(1).strip()

    if payment_due:
        fields["Payment Due"] = payment_due.group(1).strip()

    if email:
        fields["Email"] = email.group(0).strip()

    if phone:
        fields["Phone"] = phone.group(0).strip()

    if total:
        fields["Total Amount"] = total.group(1).strip()

    return fields


# =========================================================
# RESUME FIELD EXTRACTION
# =========================================================

def extract_resume_fields(text):

    fields = {}

    # -------------------------
    # Name
    # -------------------------

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    name = None

    for i, line in enumerate(lines):

        if line.upper() == "RESUME" and i + 1 < len(lines):
            name = lines[i + 1]
            break

    if name:
        fields["Name"] = name


    # -------------------------
    # Email
    # -------------------------

    email = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        text
    )

    if email:
        fields["Email"] = email.group(0).strip()


    # -------------------------
    # Phone
    # -------------------------

    phone = re.search(
        r"\+?\d[\d\s\-]{8,}\d",
        text
    )

    if phone:
        fields["Phone"] = phone.group(0).strip()


    # -------------------------
    # Education
    # -------------------------

    education = re.search(
        r"EDUCATION\s*(.*?)(?=EXPERIENCE|SKILLS|PROJECTS|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if education:
        education_text = education.group(1).strip()
        fields["Education"] = education_text


    # -------------------------
    # Experience
    # -------------------------

    experience = re.search(
        r"EXPERIENCE\s*(.*?)(?=SKILLS|PROJECTS|EDUCATION|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if experience:
        experience_text = experience.group(1).strip()
        fields["Experience"] = experience_text


    # -------------------------
    # Skills
    # -------------------------

    skills = re.search(
        r"SKILLS\s*(.*?)(?=PROJECTS|EXPERIENCE|EDUCATION|$)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if skills:

        skills_text = skills.group(1).strip()

        # Convert multiple lines into one readable line
        skill_lines = [
            line.strip()
            for line in skills_text.splitlines()
            if line.strip()
        ]

        fields["Skills"] = ", ".join(skill_lines)


    return fields


# =========================================================
# PROCESS UPLOADED DOCUMENT
# =========================================================

if uploaded_file is not None:

    st.success(
        f"File uploaded: {uploaded_file.name}"
    )


    # =====================================================
    # FILE INFORMATION
    # =====================================================

    st.write("### File Information")

    st.write(
        f"**Filename:** {uploaded_file.name}"
    )

    st.write(
        f"**File type:** {uploaded_file.type}"
    )

    st.write(
        f"**File size:** {uploaded_file.size / 1024:.2f} KB"
    )


    # =====================================================
    # EXTRACTED TEXT VARIABLE
    # =====================================================

    extracted_text = ""


    # =====================================================
    # PDF PROCESSING
    # =====================================================

    if uploaded_file.type == "application/pdf":

        pdf_bytes = uploaded_file.read()

        pdf_document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )


        # -------------------------------------------------
        # NORMAL PDF TEXT EXTRACTION
        # -------------------------------------------------

        for page in pdf_document:

            extracted_text += page.get_text()


        pdf_document.close()


        # -------------------------------------------------
        # OCR FOR SCANNED PDF
        # -------------------------------------------------

        if not extracted_text.strip():

            st.info(
                "No selectable text found. Running OCR..."
            )

            pdf_document = fitz.open(
                stream=pdf_bytes,
                filetype="pdf"
            )

            for page in pdf_document:

                pix = page.get_pixmap()

                image = Image.open(
                    io.BytesIO(
                        pix.tobytes("png")
                    )
                )

                extracted_text += (
                    pytesseract.image_to_string(image)
                )

            pdf_document.close()


    # =====================================================
    # IMAGE PROCESSING
    # =====================================================

    else:

        image = Image.open(uploaded_file)

        st.image(
            image,
            caption="Uploaded document",
            use_container_width=True
        )

        st.info(
            "Running OCR on image..."
        )

        extracted_text = pytesseract.image_to_string(
            image
        )


    # =====================================================
    # CLASSIFICATION AND FIELD EXTRACTION
    # =====================================================

    if extracted_text.strip():

        document_type = classify_document(
            extracted_text
        )


        # =================================================
        # DOCUMENT TYPE
        # =================================================

        st.write("### Document Type")


        # =================================================
        # INVOICE
        # =================================================

        if document_type == "Invoice":

            st.success("🧾 Invoice")


            invoice_fields = extract_invoice_fields(
                extracted_text
            )


            st.write("### Extracted Invoice Fields")


            if invoice_fields:

                for field, value in invoice_fields.items():

                    st.write(
                        f"**{field}:** {value}"
                    )

            else:

                st.warning(
                    "No invoice fields could be extracted."
                )


        # =================================================
        # RESUME
        # =================================================

        elif document_type == "Resume":

            st.success("📄 Resume")


            resume_fields = extract_resume_fields(
                extracted_text
            )


            st.write("### Extracted Resume Fields")


            if resume_fields:

                for field, value in resume_fields.items():

                    st.write(
                        f"**{field}:** {value}"
                    )

            else:

                st.warning(
                    "No resume fields could be extracted."
                )


        # =================================================
        # OTHER
        # =================================================

        else:

            st.info("❓ Other")

            st.write(
                "No specific fields are available for this document type."
            )


        # =================================================
        # FULL EXTRACTED TEXT
        # =================================================

        st.write("### Extracted Text")

        st.text_area(
            "Document text",
            extracted_text,
            height=400
        )


    # =====================================================
    # NO TEXT FOUND
    # =====================================================

    else:

        st.warning(
            "No text could be extracted from this document."
        )