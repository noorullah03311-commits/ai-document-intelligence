import json
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("documents.db")

WORKFLOW_STATES = ("New", "Processing", "Needs Review", "Approved", "Rejected", "Completed")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _add_column(cursor, table, column, definition):
    columns = {row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def create_database():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_filename TEXT,
            stored_filename TEXT,
            document_type TEXT,
            upload_date TEXT,
            company TEXT,
            invoice_number TEXT,
            total_amount TEXT,
            file_path TEXT,
            text_preview TEXT,
            file_hash TEXT UNIQUE,
            status TEXT
        )
    """)
    # Week 5 additions. Existing Week 4 databases are migrated automatically.
    additions = [
        ("workflow_state", "TEXT DEFAULT 'New'"),
        ("validation_errors", "TEXT DEFAULT '[]'"),
        ("review_reason", "TEXT DEFAULT ''"),
        ("predicted_confidence", "REAL"),
        ("extracted_data", "TEXT DEFAULT '{}'"),
        ("last_action", "TEXT DEFAULT 'Uploaded'"),
        ("last_action_at", "TEXT"),
        ("processing_time", "REAL"),
        ("processing_error", "INTEGER DEFAULT 0"),
    ]
    for name, definition in additions:
        _add_column(cursor, "documents", name, definition)

    cursor.execute("""
        UPDATE documents
        SET workflow_state =
            CASE
                WHEN status = 'Processed' THEN 'Completed'
                WHEN status IN ('Needs Review', 'Failed') THEN 'Needs Review'
                WHEN status IN ('New','Processing','Approved','Rejected','Completed') THEN status
                ELSE 'New'
            END
        WHERE workflow_state IS NULL OR workflow_state = ''
    """)
    cursor.execute("""
        UPDATE documents
        SET processing_error = 1
        WHERE status = 'Failed' AND (processing_error IS NULL OR processing_error = 0)
    """)
    cursor.execute("""
        UPDATE documents
        SET last_action = CASE
            WHEN workflow_state = 'Completed' THEN 'Completed'
            WHEN workflow_state = 'Needs Review' THEN 'Sent to Review'
            ELSE 'Uploaded'
        END
        WHERE last_action IS NULL OR last_action = ''
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            previous_status TEXT,
            new_status TEXT,
            timestamp TEXT NOT NULL,
            reason TEXT DEFAULT '',
            FOREIGN KEY(document_id) REFERENCES documents(id)
        )
    """)
    connection.commit()
    connection.close()


def insert_document(original_filename, stored_filename, document_type, upload_date,
                    company, invoice_number, total_amount, file_path, text_preview,
                    file_hash, status="New", workflow_state="New",
                    validation_errors=None, review_reason="", predicted_confidence=None,
                    extracted_data=None, last_action="Uploaded", processing_time=None,
                    processing_error=0):
    validation_errors = validation_errors or []
    extracted_data = extracted_data or {}
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO documents (
            original_filename, stored_filename, document_type, upload_date,
            company, invoice_number, total_amount, file_path, text_preview,
            file_hash, status, workflow_state, validation_errors, review_reason,
            predicted_confidence, extracted_data, last_action, last_action_at,
            processing_time, processing_error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        original_filename, stored_filename, document_type, upload_date,
        company, invoice_number, total_amount, file_path, text_preview,
        file_hash, status, workflow_state, json.dumps(validation_errors),
        review_reason, predicted_confidence, json.dumps(extracted_data),
        last_action, upload_date, processing_time, int(processing_error)
    ))
    document_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return document_id


def update_document_workflow(document_id, workflow_state, validation_errors=None,
                             review_reason=None, last_action=None, processing_time=None,
                             processing_error=None, extracted_data=None,
                             predicted_confidence=None):
    connection = get_connection()
    cursor = connection.cursor()
    fields, values = ["workflow_state = ?", "status = ?"], [workflow_state, workflow_state]
    if validation_errors is not None:
        fields.append("validation_errors = ?"); values.append(json.dumps(validation_errors))
    if review_reason is not None:
        fields.append("review_reason = ?"); values.append(review_reason)
    if last_action is not None:
        fields.append("last_action = ?"); values.append(last_action)
        fields.append("last_action_at = ?"); values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if processing_time is not None:
        fields.append("processing_time = ?"); values.append(processing_time)
    if processing_error is not None:
        fields.append("processing_error = ?"); values.append(int(processing_error))
    if extracted_data is not None:
        fields.append("extracted_data = ?"); values.append(json.dumps(extracted_data))
    if predicted_confidence is not None:
        fields.append("predicted_confidence = ?"); values.append(predicted_confidence)
    values.append(document_id)
    cursor.execute(f"UPDATE documents SET {', '.join(fields)} WHERE id = ?", values)
    connection.commit()
    connection.close()


def update_document_fields(document_id, **fields):
    allowed = {
        "document_type", "company", "invoice_number", "total_amount",
        "text_preview", "extracted_data", "predicted_confidence"
    }
    clean = {k: v for k, v in fields.items() if k in allowed}
    if "extracted_data" in clean and isinstance(clean["extracted_data"], dict):
        clean["extracted_data"] = json.dumps(clean["extracted_data"])
    if not clean:
        return
    assignments = ", ".join(f"{k} = ?" for k in clean)
    connection = get_connection()
    connection.execute(f"UPDATE documents SET {assignments} WHERE id = ?", [*clean.values(), document_id])
    connection.commit()
    connection.close()


def get_all_documents():
    connection = get_connection()
    rows = connection.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_document_by_id(document_id):
    connection = get_connection()
    row = connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    connection.close()
    return dict(row) if row else None


def document_hash_exists(file_hash):
    connection = get_connection()
    row = connection.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,)).fetchone()
    connection.close()
    return dict(row) if row else None


def search_documents(search_text="", workflow_state="All"):
    connection = get_connection()
    value = f"%{search_text}%"
    query = """
        SELECT * FROM documents
        WHERE (
            original_filename LIKE ? OR company LIKE ? OR invoice_number LIKE ?
            OR document_type LIKE ? OR text_preview LIKE ?
        )
    """
    params = [value] * 5
    if workflow_state != "All":
        query += " AND workflow_state = ?"
        params.append(workflow_state)
    query += " ORDER BY id DESC"
    rows = connection.execute(query, params).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_filtered_documents(document_type="All", status="All", upload_date=None,
                           sort_order="Newest", workflow_state=None, search_text=""):
    connection = get_connection()
    query = "SELECT * FROM documents WHERE 1=1"
    values = []
    if document_type != "All":
        query += " AND document_type = ?"; values.append(document_type)
    if status != "All":
        query += " AND status = ?"; values.append(status)
    if workflow_state and workflow_state != "All":
        query += " AND workflow_state = ?"; values.append(workflow_state)
    if upload_date:
        query += " AND DATE(upload_date) = ?"; values.append(str(upload_date))
    if search_text:
        value = f"%{search_text}%"
        query += """ AND (original_filename LIKE ? OR company LIKE ? OR invoice_number LIKE ?
                    OR document_type LIKE ? OR text_preview LIKE ?)"""
        values.extend([value] * 5)
    query += " ORDER BY upload_date ASC, id ASC" if sort_order == "Oldest" else " ORDER BY upload_date DESC, id DESC"
    rows = connection.execute(query, values).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_metrics():
    connection = get_connection()
    total = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    processed = connection.execute("SELECT COUNT(*) FROM documents WHERE workflow_state='Completed'").fetchone()[0]
    review = connection.execute("SELECT COUNT(*) FROM documents WHERE workflow_state='Needs Review'").fetchone()[0]
    approved = connection.execute("SELECT COUNT(*) FROM documents WHERE workflow_state='Approved'").fetchone()[0]
    rejected = connection.execute("SELECT COUNT(*) FROM documents WHERE workflow_state='Rejected'").fetchone()[0]
    failed = connection.execute("SELECT COUNT(*) FROM documents WHERE processing_error=1").fetchone()[0]
    types = connection.execute("SELECT document_type, COUNT(*) AS count FROM documents GROUP BY document_type").fetchall()
    connection.close()
    return {
        "total": total, "processed": processed, "review": review,
        "approved": approved, "rejected": rejected, "failed": failed,
        "types": {row["document_type"] or "Unknown": row["count"] for row in types}
    }


def get_latest_audit(document_id):
    connection = get_connection()
    row = connection.execute("""
        SELECT * FROM audit_log WHERE document_id = ?
        ORDER BY id DESC LIMIT 1
    """, (document_id,)).fetchone()
    connection.close()
    return dict(row) if row else None


def get_audit_history(document_id):
    connection = get_connection()
    rows = connection.execute("""
        SELECT * FROM audit_log WHERE document_id = ?
        ORDER BY id ASC
    """, (document_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def delete_document(document_id):
    connection = get_connection()
    connection.execute("DELETE FROM audit_log WHERE document_id = ?", (document_id,))
    connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully.")
