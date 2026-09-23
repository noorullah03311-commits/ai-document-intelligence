import sqlite3
from pathlib import Path

DB_PATH = Path("documents.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


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

    connection.commit()
    connection.close()


def insert_document(
    original_filename,
    stored_filename,
    document_type,
    upload_date,
    company,
    invoice_number,
    total_amount,
    file_path,
    text_preview,
    file_hash,
    status
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO documents (
            original_filename,
            stored_filename,
            document_type,
            upload_date,
            company,
            invoice_number,
            total_amount,
            file_path,
            text_preview,
            file_hash,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        original_filename,
        stored_filename,
        document_type,
        upload_date,
        company,
        invoice_number,
        total_amount,
        file_path,
        text_preview,
        file_hash,
        status
    ))

    connection.commit()
    connection.close()


def get_all_documents():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM documents
        ORDER BY id DESC
    """)

    documents = cursor.fetchall()

    connection.close()

    return documents


def get_document_by_id(document_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM documents
        WHERE id = ?
    """, (document_id,))

    document = cursor.fetchone()

    connection.close()

    return document


def document_hash_exists(file_hash):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM documents
        WHERE file_hash = ?
    """, (file_hash,))

    document = cursor.fetchone()

    connection.close()

    return document


def search_documents(search_text):
    connection = get_connection()
    cursor = connection.cursor()

    search_value = f"%{search_text}%"

    cursor.execute("""
        SELECT * FROM documents
        WHERE original_filename LIKE ?
           OR company LIKE ?
           OR invoice_number LIKE ?
           OR document_type LIKE ?
           OR text_preview LIKE ?
        ORDER BY id DESC
    """, (
        search_value,
        search_value,
        search_value,
        search_value,
        search_value
    ))

    documents = cursor.fetchall()

    connection.close()

    return documents


# =========================================================
# TASK 5: FILTERS AND SORTING
# =========================================================

def get_filtered_documents(
    document_type="All",
    status="All",
    upload_date=None,
    sort_order="Newest"
):
    connection = get_connection()
    cursor = connection.cursor()

    query = "SELECT * FROM documents WHERE 1=1"
    values = []

    if document_type != "All":
        query += " AND document_type = ?"
        values.append(document_type)

    if status != "All":
        query += " AND status = ?"
        values.append(status)

    if upload_date:
        query += " AND DATE(upload_date) = ?"
        values.append(str(upload_date))

    if sort_order == "Oldest":
        query += " ORDER BY upload_date ASC, id ASC"
    else:
        query += " ORDER BY upload_date DESC, id DESC"

    cursor.execute(query, values)

    documents = cursor.fetchall()

    connection.close()

    return documents


def delete_document(document_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM documents
        WHERE id = ?
    """, (document_id,))

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully.")