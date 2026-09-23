AI Document Intelligence & Workflow Platform

ZYROO AI/ML Internship Program — Week 4

An AI-powered document management system built with Python and Streamlit. The platform extracts text from documents, classifies them, extracts important fields, stores files and metadata, detects duplicates, and supports document search and filtering.

Features

- Upload PDF, JPG, JPEG, and PNG documents.
- Extract text from PDFs and scanned documents using OCR.
- Clean extracted text.
- Classify documents as Invoice, Resume, or Other.
- Extract important invoice and resume information.
- Store documents in organized folders.
- Generate safe filenames for stored documents.
- Store document metadata in an SQLite database.
- Detect duplicate files using SHA-256 hashing.
- Search documents by filename, company, invoice number, type, or text.
- Filter documents by type, processing status, and upload date.
- Sort documents by newest or oldest.
- View document details and download saved files.
- Track processing status: Processed, Needs Review, or Failed.
- Validate uploads and display user-friendly error messages.

Technologies Used

- Python
- Streamlit
- SQLite
- PyMuPDF
- Pytesseract
- Pillow
- Scikit-learn
- Hashlib

Project Structure

ai-document-intelligence/
│
├── app.py
├── database.py
├── storage_manager.py
├── test_repository.py
├── train_model.py
├── requirements.txt
├── README.md
├── documents.db
│
├── storage/
│   ├── invoices/
│   ├── resumes/
│   └── other/
│
└── dataset/
    └── week3_dataset/

Note: The database, storage folders, and dataset may be created or populated as the application is used. The exact project structure may vary.

Installation

1. Install Python

Install Python 3 from:

https://www.python.org/downloads/

During installation on Windows, enable Add Python to PATH.

2. Install dependencies

Open the terminal in the project folder and run:

pip install -r requirements.txt

3. Install Tesseract OCR

Tesseract OCR is required for scanned documents and images.

Install Tesseract OCR for your operating system. Make sure it is configured correctly so Pytesseract can access it.

4. Run the application

streamlit run app.py

The application will open in your browser.

How to Use

1. Run the Streamlit application.
2. Upload a supported document.
3. The system validates and hashes the file.
4. Duplicate files are detected before saving.
5. Text is extracted and cleaned.
6. The document is classified.
7. Important fields are extracted where applicable.
8. The file is saved in structured storage.
9. Metadata and processing status are saved in SQLite.
10. Use search, filters, sorting, and Document Detail View to manage saved documents.

Database

The project uses SQLite with a "documents" table.

Stored metadata includes:

- Document ID
- Original filename
- Stored filename
- Document type
- Upload date
- Company
- Invoice number
- Total amount
- File path
- Text preview
- SHA-256 file hash
- Processing status

Processing Status

Status| Meaning
Processed| Document processing completed successfully
Needs Review| Important information is missing or requires manual review
Failed| Document processing could not be completed

Duplicate Detection

The system generates a SHA-256 hash from the uploaded file's bytes. If the hash already exists in the database, the application identifies the duplicate and avoids saving another copy.

Supported File Types

- PDF
- JPG
- JPEG
- PNG

Maximum upload size: 10 MB.

Run Repository Tests

To run the repository test suite:

python test_repository.py

The test script checks database creation, sample document insertion, document types, duplicate hash lookup, search, filtering, sorting, document lookup, and persistence after reconnecting.

The test uses a temporary database and does not intentionally modify the main project database.

Project Status

Week 4 focuses on building a document management layer on top of the document processing pipeline, including structured storage, SQLite metadata, duplicate detection, search, filtering, document details, processing status, safer error handling, and repository testing.

Author

Mehboob Alam

ZYROO AI/ML Internship Program