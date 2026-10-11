# AI Document Intelligence & Workflow Platform

**ZYROO AI/ML Internship — Week 6: Final Integration, Optimization & Project Completion**

A local Streamlit application that stores documents, extracts PDF text or OCR text from scanned PDFs/images, classifies documents, extracts supported fields, validates them, applies workflow rules, and records review decisions and audit events in SQLite.

## Product flow

Upload → File checks → PDF text extraction/OCR → Classification → Field extraction → Validation → Workflow decision → Human review → Audit → Search and dashboard.

## Features

- Upload checks for PDF/JPG/JPEG/PNG, empty files, file size (10 MB), and basic file signatures.
- SHA-256 duplicate detection; duplicate attempts are counted in the dashboard.
- Random internal filenames and separate invoice/resume/other storage folders.
- Digital PDF text extraction and Tesseract OCR for scanned PDFs and images.
- Cached TF-IDF + Multinomial Naive Bayes model, so it is not retrained on every document.
- Invoice/resume field extraction and validation.
- Workflow states: New, Processing, Needs Review, Approved, Rejected, Completed.
- Review decisions, rejection reasons, audit trail, batch processing, search, filters and metrics.
- SQLite migrations preserve existing Week 4/5 databases.
- Local document Q&A uses TF-IDF retrieval over stored text, shows source document IDs/names and supporting excerpts, and abstains when relevance is too low. No external API key is required.
- User-facing processing errors and automated tests.

## Requirements

- Python 3.10+ recommended (use a Python version supported by your installed scikit-learn and Streamlit releases).
- Tesseract OCR installed and available on your system PATH for scanned PDFs/images.
- The PDF/image packages listed in `requirements.txt`.

## Install and run on macOS

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
streamlit run app.py
```

If your existing `.venv` already works, activate it and run `python3 -m pip install -r requirements.txt` followed by `streamlit run app.py`.

Install Tesseract separately if needed. On a Mac with Homebrew:

```bash
brew install tesseract
```

## Run tests

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

Tests cover the Week 5 workflow/validation/database requirements plus Week 6 upload checks, corrupt PDFs, safe filenames, classifier probabilities, duplicate metrics, and persistence.

## Configuration

The app works without a `.env` file. Optional environment variables are documented in `.env.example`:

- `AI_DOC_DATABASE_PATH`: absolute path for the SQLite database.
- `AI_DOC_STORAGE_DIR`: absolute path for stored documents.

Set them in the terminal before starting Streamlit if you need custom locations. Do not commit secrets or private documents.

## Supported types and extracted fields

- **Invoice:** invoice number, date, company, total amount, email, phone.
- **Resume/CV:** name, email, phone, skills.
- **Other:** classification only; no category-specific fields are required.

The classifier loads labeled `.txt` files from `dataset/week3_dataset/Invoice`, `Resume`, and `Other`. If fewer than three examples or fewer than two categories are available, it uses a small built-in fallback corpus so the demo remains runnable. This fallback is only for demonstration; evaluate with a representative, labeled dataset before claiming model accuracy. The model is cached for the running app. Restart the app or call `clear_model_cache()` after changing training files.

## Workflow rules

- Invalid or missing required fields route a document to **Needs Review**.
- Classification confidence below 70% routes a document to **Needs Review** when confidence is available.
- A reviewer can approve or reject a document in the review queue; rejection requires a reason.
- Invalid state transitions are blocked and workflow actions are written to the audit log.

## Evaluation results

Run `python3 -m pytest -q`; the Week 6 preparation environment completed 15 tests successfully. Rerun in your own Mac environment and record that actual output at submission time. Do not claim accuracy or test coverage that has not been measured. The automated suite checks software behavior; it does not establish real-world OCR or classification accuracy.

## Known limitations

- Extraction uses regular expressions and may miss unusual layouts, tables, handwritten content, or fields with unexpected labels.
- The Q&A page is a lightweight local TF-IDF retrieval assistant, not a generative LLM or embedding-based RAG system. It returns source passages rather than synthesizing answers; semantic retrieval quality is limited by TF-IDF and the quality of extracted text.
- Authentication and role-based access are not implemented; use only on a trusted local machine with documents you are authorized to process.
- Basic file signatures and parser checks help catch malformed uploads but are not a complete malware scanner.
- The built-in classifier fallback corpus is small and is not suitable for production evaluation.

## Final demo checklist

1. Start the app and upload a digital PDF.
2. Upload a scanned PDF or image with Tesseract installed.
3. Show extracted fields, confidence, validation results, and workflow state.
4. Upload the same file again and show duplicate detection/metrics.
5. Review a document and approve or reject it (provide a reason for rejection).
6. Show audit history, search/filter, batch processing, and the dashboard.
7. Run the automated tests and retain the actual terminal output as evidence.

## Project structure

- `app.py` — Streamlit pages and user interactions
- `assistant.py` — chunking, TF-IDF retrieval, source references and abstention
- `file_security.py` — upload size/type/signature checks
- `processor.py` — PDF/image reading and OCR
- `classifier.py` — cached text classifier
- `extractor.py` / `validator.py` — field extraction and validation
- `workflow.py` — allowed transitions and decision rules
- `database.py` / `audit.py` — SQLite persistence and audit history
- `storage_manager.py` / `file_security.py` — safe storage and upload checks
- `test_week5.py` / `test_week6.py` — automated tests

## Architecture overview

```text
Streamlit UI (app.py)
  ├── Upload checks (file_security.py) ── SHA-256 duplicate check
  ├── PDF/Image extraction + OCR (processor.py)
  ├── TF-IDF classifier (classifier.py) ── field extraction (extractor.py)
  ├── Validation + workflow rules (validator.py, workflow.py)
  ├── Safe file storage (storage_manager.py)
  ├── SQLite records + audit log (database.py, audit.py)
  └── Local source-grounded Q&A (assistant.py)
```
