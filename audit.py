from datetime import datetime
from database import get_connection


def log_event(document_id, action, previous_status, new_status, reason=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    connection = get_connection()
    connection.execute("""
        INSERT INTO audit_log
        (document_id, action, previous_status, new_status, timestamp, reason)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (document_id, action, previous_status, new_status, timestamp, reason))
    connection.commit()
    connection.close()
    return timestamp


def get_history(document_id):
    connection = get_connection()
    rows = connection.execute("""
        SELECT id, document_id, action, previous_status, new_status, timestamp, reason
        FROM audit_log
        WHERE document_id = ?
        ORDER BY id ASC
    """, (document_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]
