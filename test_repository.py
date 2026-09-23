import tempfile
import os
from pathlib import Path

import database


# =====================================================
# TASK 9: REPOSITORY TESTING
# =====================================================

def run_tests():

    print("\nStarting Week 4 Repository Tests...\n")

    # Use a temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(
        suffix=".db",
        delete=False
    )

    temp_db.close()

    database.DB_PATH = Path(temp_db.name)

    try:

        # ---------------------------------------------
        # TEST 1: Create database
        # ---------------------------------------------

        database.create_database()

        print("TEST 1 PASSED: Database created.")

        # ---------------------------------------------
        # TEST 2: Insert 10 sample documents
        # ---------------------------------------------

        sample_documents = []

        for i in range(1, 11):

            if i % 3 == 0:
                doc_type = "Resume"
            elif i % 3 == 1:
                doc_type = "Invoice"
            else:
                doc_type = "Other"

            if i == 10:
                status = "Failed"
            elif i == 9:
                status = "Needs Review"
            else:
                status = "Processed"

            document = {
                "original_filename": f"test_doc_{i}.pdf",
                "stored_filename": f"safe_{i}.pdf",
                "document_type": doc_type,
                "upload_date": f"2026-09-{i:02d} 10:00:00",
                "company": f"Company{i}",
                "invoice_number": f"INV-{i}",
                "total_amount": str(i * 100),
                "file_path": f"storage/test/safe_{i}.pdf",
                "text_preview": f"Sample document text {i}",
                "file_hash": f"hash_test_{i}",
                "status": status
            }

            sample_documents.append(document)

            database.insert_document(**document)

        all_docs = database.get_all_documents()

        assert len(all_docs) == 10

        print("TEST 2 PASSED: 10 documents inserted.")

        # ---------------------------------------------
        # TEST 3: Test document types
        # ---------------------------------------------

        types_found = {
            doc[3] for doc in all_docs
        }

        assert "Invoice" in types_found
        assert "Resume" in types_found
        assert "Other" in types_found

        print("TEST 3 PASSED: All document types exist.")

        # ---------------------------------------------
        # TEST 4: Duplicate hash detection
        # ---------------------------------------------

        duplicate = database.document_hash_exists(
            "hash_test_1"
        )

        assert duplicate is not None

        assert duplicate[1] == "test_doc_1.pdf"

        print("TEST 4 PASSED: Duplicate hash detected.")

        # ---------------------------------------------
        # TEST 5: Search documents
        # ---------------------------------------------

        search_results = database.search_documents(
            "Company1"
        )

        assert len(search_results) >= 1

        print("TEST 5 PASSED: Search is working.")

        # ---------------------------------------------
        # TEST 6: Filter by document type
        # ---------------------------------------------

        invoices = database.get_filtered_documents(
            document_type="Invoice"
        )

        assert len(invoices) > 0

        assert all(
            doc[3] == "Invoice"
            for doc in invoices
        )

        print("TEST 6 PASSED: Type filter works.")

        # ---------------------------------------------
        # TEST 7: Filter by processing status
        # ---------------------------------------------

        failed_docs = database.get_filtered_documents(
            status="Failed"
        )

        assert len(failed_docs) == 1

        assert failed_docs[0][11] == "Failed"

        print("TEST 7 PASSED: Status filter works.")

        # ---------------------------------------------
        # TEST 8: Test sorting
        # ---------------------------------------------

        newest = database.get_filtered_documents(
            sort_order="Newest"
        )

        oldest = database.get_filtered_documents(
            sort_order="Oldest"
        )

        assert len(newest) == 10
        assert len(oldest) == 10

        assert oldest[0][4] <= oldest[-1][4]

        print("TEST 8 PASSED: Sorting works.")

        # ---------------------------------------------
        # TEST 9: Document detail lookup
        # ---------------------------------------------

        document = database.get_document_by_id(1)

        assert document is not None

        assert document[1] == "test_doc_1.pdf"

        print("TEST 9 PASSED: Document detail lookup works.")

        # ---------------------------------------------
        # TEST 10: Database persistence
        # ---------------------------------------------

        # Simulate reconnecting to the database
        database.create_database()

        documents_after_restart = database.get_all_documents()

        assert len(documents_after_restart) == 10

        print("TEST 10 PASSED: Records persist after reconnect.")

        # ---------------------------------------------
        # FINAL RESULT
        # ---------------------------------------------

        print("\n===================================")
        print("ALL 10 REPOSITORY TESTS PASSED!")
        print("Week 4 Task 9 testing completed.")
        print("===================================")

    finally:

        # Close and remove temporary test database
        if os.path.exists(temp_db.name):
            os.remove(temp_db.name)


if __name__ == "__main__":
    run_tests()