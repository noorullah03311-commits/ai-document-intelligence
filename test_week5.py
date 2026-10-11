import json
import tempfile
from pathlib import Path

import database
from validator import validate_document
from workflow import apply_rules, can_transition, LOW_CONFIDENCE_THRESHOLD


def test_workflow_transitions():
    assert can_transition("New", "Processing")
    assert can_transition("Processing", "Needs Review")
    assert can_transition("Needs Review", "Approved")
    assert can_transition("Needs Review", "Rejected")
    assert can_transition("Approved", "Completed")
    assert not can_transition("Completed", "Processing")
    assert not can_transition("Rejected", "Completed")


def test_invoice_validation():
    valid = {
        "Invoice Number": "INV-100",
        "Date": "06/10/2026",
        "Company": "ABC Ltd",
        "Total Amount": "PKR 1000",
        "Email": "abc@example.com",
        "Phone": "+923001234567",
    }
    result = validate_document("Invoice", valid)
    assert result["valid"] is True
    assert result["errors"] == []


def test_invalid_invoice():
    result = validate_document("Invoice", {
        "Invoice Number": "INV-100",
        "Date": "bad-date",
        "Company": "ABC Ltd",
        "Total Amount": "not-an-amount",
        "Email": "bad-email",
        "Phone": "123",
    })
    assert result["valid"] is False
    assert result["errors"]


def test_low_confidence_rule():
    validation = validate_document("Other", {})
    result = apply_rules("Other", validation, LOW_CONFIDENCE_THRESHOLD - 0.01)
    assert result["next_state"] == "Needs Review"


def test_database_creation():
    old_path = database.DB_PATH
    with tempfile.TemporaryDirectory() as tmp:
        database.DB_PATH = Path(tmp) / "test.db"
        database.create_database()
        connection = database.get_connection()
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(documents)").fetchall()}
        connection.close()
        assert "workflow_state" in columns
        assert "validation_errors" in columns
        assert "predicted_confidence" in columns
        database.DB_PATH = old_path


if __name__ == "__main__":
    tests = [
        test_workflow_transitions,
        test_invoice_validation,
        test_invalid_invoice,
        test_low_confidence_rule,
        test_database_creation,
    ]
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print("All Week 5 tests passed.")
