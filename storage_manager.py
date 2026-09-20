import uuid
from pathlib import Path


STORAGE_DIR = Path("storage")

FOLDERS = {
    "invoice": STORAGE_DIR / "invoices",
    "resume": STORAGE_DIR / "resumes",
    "other": STORAGE_DIR / "other"
}


def create_storage_folders():
    for folder in FOLDERS.values():
        folder.mkdir(parents=True, exist_ok=True)


def get_safe_filename(original_filename):
    extension = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4().hex}{extension}"


def get_storage_path(document_type, original_filename):
    create_storage_folders()

    folder = FOLDERS.get(document_type, FOLDERS["other"])
    safe_filename = get_safe_filename(original_filename)

    return folder / safe_filename