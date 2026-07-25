import os
import uuid
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
UPLOAD_DIR = Path("uploads")


def secure_filename(original_name: str) -> str:
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return safe_name


def save_upload(file_content: bytes, original_name: str) -> str:
    if len(file_content) > MAX_UPLOAD_SIZE:
        raise ValueError(f"File exceeds maximum size of {MAX_UPLOAD_SIZE // (1024*1024)}MB")
    safe_name = secure_filename(original_name)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = str(UPLOAD_DIR / safe_name)
    with open(file_path, "wb") as f:
        f.write(file_content)
    return file_path
