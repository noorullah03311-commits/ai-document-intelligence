"""Safe document storage with optional AI_DOC_STORAGE_DIR configuration."""
import os
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = Path(os.getenv("AI_DOC_STORAGE_DIR", str(BASE_DIR / "storage"))).expanduser().resolve()
FOLDERS = {
    "invoice": STORAGE_DIR / "invoices",
    "resume": STORAGE_DIR / "resumes",
    "other": STORAGE_DIR / "other",
}


def create_storage_folders():
    for folder in FOLDERS.values():
        folder.mkdir(parents=True, exist_ok=True)


def get_safe_filename(original_filename):
    # Only retain a short, simple extension; never use user-provided path segments.
    extension = Path(str(original_filename)).suffix.lower()
    if len(extension) > 10 or not extension.startswith(".") or not extension[1:].isalnum():
        extension = ""
    return f"{uuid.uuid4().hex}{extension}"


def get_storage_path(document_type, original_filename):
    create_storage_folders()
    folder = FOLDERS.get(str(document_type).lower(), FOLDERS["other"])
    path = (folder / get_safe_filename(original_filename)).resolve()
    if path.parent != folder.resolve():
        raise ValueError("Unsafe storage path rejected.")
    return path
