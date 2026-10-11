"""Week 6 reliability and security tests. Run with: python -m pytest -q"""
import io
import tempfile
from pathlib import Path

import database
from classifier import classify_document
from file_security import validate_upload
from processor import process_document
from storage_manager import get_safe_filename
from validator import validate_document
from workflow import can_transition, transition_or_raise


def test_valid_pdf_signature_and_bad_signature():
    assert validate_upload("invoice.pdf", b"%PDF-1.7 sample") is None
    assert "valid PDF" in validate_upload("invoice.pdf", b"not a pdf")


def test_unsupported_empty_and_oversized_uploads():
    assert "Unsupported" in validate_upload("script.exe", b"data")
    assert "empty" in validate_upload("empty.pdf", b"")
    assert "10 MB" in validate_upload("big.pdf", b"%PDF-" + b"x" * (10 * 1024 * 1024 + 1))


def test_safe_storage_filename_does_not_keep_path():
    name = get_safe_filename("../../secret/invoice.PDF")
    assert "/" not in name and "\\" not in name
    assert name.endswith(".pdf")
    assert "secret" not in name


def test_corrupt_pdf_returns_clear_error():
    try:
        process_document(b"not a pdf", "bad.pdf")
    except ValueError as exc:
        assert "damaged" in str(exc).lower() or "cannot be opened" in str(exc).lower()
    else:
        raise AssertionError("Corrupt PDF should not process successfully")


def test_classifier_returns_real_probabilities_and_handles_empty_text():
    label, confidence, probabilities = classify_document("Invoice Number INV-1 Total Amount PKR 400")
    assert label in {"Invoice", "Resume", "Other"}
    assert confidence is not None and 0 <= confidence <= 1
    assert abs(sum(probabilities.values()) - 1) < 1e-6
    assert classify_document(" ") == ("Other", None, {})


def test_workflow_invalid_transition_is_blocked():
    assert not can_transition("Completed", "Processing")
    try:
        transition_or_raise("Completed", "Processing")
    except ValueError as exc:
        assert "Invalid workflow transition" in str(exc)
    else:
        raise AssertionError("Invalid transition should raise ValueError")


def test_duplicate_metrics_and_database_persistence():
    original = database.DB_PATH
    with tempfile.TemporaryDirectory() as tmp:
        database.DB_PATH = Path(tmp) / "test.db"
        try:
            database.create_database()
            document_id = database.insert_document(
                original_filename="invoice.pdf", stored_filename="safe.pdf",
                document_type="Invoice", upload_date="2026-10-10 12:00:00",
                company="Example Ltd", invoice_number="INV-1", total_amount="100",
                file_path="", text_preview="Invoice INV-1", file_hash="abc123",
            )
            database.log_duplicate("copy.pdf", "abc123", document_id)
            assert database.document_hash_exists("abc123")["id"] == document_id
            assert database.get_metrics()["duplicates"] == 1
            database.create_database()  # Simulates an application restart/reconnect.
            assert database.get_document_by_id(document_id)["original_filename"] == "invoice.pdf"
            assert len(database.get_recent_activity()) == 0
        finally:
            database.DB_PATH = original


def test_invoice_validation_missing_fields_are_reported():
    result = validate_document("Invoice", {"Invoice Number": "", "Date": "bad"})
    assert result["valid"] is False
    assert "Company" in result["missing_fields"]
    assert result["errors"]


def test_digital_pdf_text_extraction():
    import fitz
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Invoice Number INV-2026 Total Amount PKR 1250")
    pdf_bytes = document.tobytes()
    document.close()
    text = process_document(pdf_bytes, "sample.pdf")
    assert "INV-2026" in text
    assert "1250" in text


def test_document_qa_cites_source_and_abstains_when_unknown():
    from assistant import answer_question, chunk_text
    docs = [{
        "id": 7,
        "original_filename": "invoice_7.pdf",
        "full_text": "Invoice INV-700. Total amount is PKR 4500. Payment is due on 15 October.",
        "text_preview": "",
    }]
    result = answer_question("What is the total amount?", docs)
    assert result["sources"]
    assert result["sources"][0]["document_id"] == 7
    assert "4500" in result["answer"]
    unknown = answer_question("Who won the football world cup?", docs)
    assert unknown["sources"] == []
    assert "couldn't find enough" in unknown["answer"]
    assert chunk_text("one two three", max_chars=5, overlap=1)
