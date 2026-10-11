"""Repository smoke tests for database insert, search, duplicate tracking and restart persistence."""
import tempfile
from pathlib import Path

import database


def test_repository_end_to_end():
    original_path = database.DB_PATH
    with tempfile.TemporaryDirectory() as temp_dir:
        database.DB_PATH = Path(temp_dir) / "repository_test.db"
        try:
            database.create_database()
            document_id = database.insert_document(
                original_filename="test_invoice.pdf",
                stored_filename="safe123.pdf",
                document_type="Invoice",
                upload_date="2026-10-10 10:00:00",
                company="Example Ltd",
                invoice_number="INV-100",
                total_amount="1000",
                file_path="",
                text_preview="Invoice INV-100 total amount 1000",
                file_hash="unique-test-hash",
            )
            assert database.get_document_by_id(document_id)["original_filename"] == "test_invoice.pdf"
            assert database.search_documents("INV-100")
            assert database.get_filtered_documents(document_type="Invoice")
            database.log_duplicate("duplicate.pdf", "unique-test-hash", document_id)
            assert database.get_metrics()["duplicates"] == 1
            database.create_database()
            assert database.get_document_by_id(document_id)["workflow_state"] == "New"
        finally:
            database.DB_PATH = original_path
