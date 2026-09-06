# 📄 AI Document Intelligence

An AI-powered document processing application built with Python and Streamlit.

The application can upload PDF and image documents, extract text using PDF text extraction and OCR, classify documents, and extract important information from invoices and resumes.

---

## 🚀 Features

- Upload PDF, JPG, JPEG, and PNG documents
- Extract text from normal PDFs using PyMuPDF
- Extract text from scanned PDFs using Tesseract OCR
- Extract text from images using Tesseract OCR
- Classify documents into:
  - Invoice
  - Resume
  - Other
- Extract important invoice information
- Extract important resume information
- Display complete extracted text
- Simple Streamlit web interface

---

## 🧾 Invoice Information

The application can extract:

- Invoice Number
- Date
- Company Name
- Payment Due
- Email
- Phone
- Total Amount

---

## 📄 Resume Information

The application can extract:

- Name
- Email
- Phone
- Education
- Experience
- Skills

---

## 🛠️ Technologies Used

- Python
- Streamlit
- PyMuPDF
- Tesseract OCR
- Pytesseract
- Pillow
- Regular Expressions (Regex)

---

## 📁 Project Structure

```text
ai-document-intelligence/
│
├── app.py
├── requirements.txt
├── README.md
│
├── samples/
│   ├── invoice1
│   ├── invoice2
│   └── resume1
│
└── venv/