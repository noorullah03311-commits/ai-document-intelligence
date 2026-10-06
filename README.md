# AI Document Intelligence & Workflow Platform

## ZYROO AI/ML Internship — Week 5

Week 5 upgrades the Week 4 document manager into a controlled workflow platform.

### Week 5 workflow

Upload → Process → Classify → Extract → Validate → Apply Rules → Review / Approve / Reject → Complete → Audit History

### Main features

- Workflow states: New, Processing, Needs Review, Approved, Rejected, Completed.
- SQLite workflow state management.
- Invalid workflow transitions are blocked.
- Invoice validation for Invoice Number, Date, Company Name and Total Amount.
- Resume validation for Name, Email and Skills.
- Email, phone, date and numeric amount format checks.
- Exact validation failures are stored.
- Separate rule-based workflow engine in `workflow.py`.
- Confidence-aware review using the classifier's real `predict_proba()` output.
- Low-confidence threshold is documented in `workflow.py`.
- Human review queue with Approve and Reject.
- Rejection requires a reason.
- Full audit history in SQLite.
- Batch processing with individual results.
- One failed document does not stop the batch.
- Workflow search and state filters.
- Latest workflow action and timestamp.
- Metrics dashboard.
- Reliability testing checklist and automated Week 5 tests.
- Existing Week 4 OCR, storage, duplicate hashing and document search are retained.

## Files

- `app.py` — Streamlit interface and pages
- `database.py` — SQLite schema, migration, queries and metrics
- `storage_manager.py` — safe file storage
- `processor.py` — PDF/image extraction and OCR
- `classifier.py` — TF-IDF + Naive Bayes classification with real confidence
- `extractor.py` — invoice/resume field extraction
- `validator.py` — document validation rules
- `workflow.py` — states, transitions and automated decisions
- `audit.py` — workflow audit logging
- `test_week5.py` — Week 5 automated tests
- `train_model.py` — existing Week 3/4 model evaluation script

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure Tesseract OCR is installed and available to `pytesseract`.

Start Streamlit:

```bash
streamlit run app.py
```

Run Week 5 tests:

```bash
python test_week5.py
```

## Database migration

The application automatically adds the Week 5 columns to an existing Week 4 `documents.db`. Existing `Processed` records are mapped to `Completed`, while old `Needs Review` and `Failed` records are placed in `Needs Review` with the failure flag retained where applicable.

## Confidence

The classifier only stores confidence when the model actually provides `predict_proba()`. No artificial confidence value is created. The review threshold is `70%` and is defined as `LOW_CONFIDENCE_THRESHOLD` in `workflow.py`.

## Testing

The Week 5 assignment calls for testing normal invoices/resumes, missing fields, unreadable/scanned documents, duplicates, invalid formats, low confidence when available, database/storage failures, invalid transitions and mixed-success batches. Use the Reliability Testing page and `test_week5.py` to document the testing evidence.

## Author

Mehboob Alam  
ZYROO AI/ML Internship Program
