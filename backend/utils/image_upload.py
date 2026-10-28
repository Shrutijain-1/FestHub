"""Saves and deletes uploaded event images."""
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_BYTES = 2 * 1024 * 1024  # 2 MB


def _looks_like_image(content: bytes, extension: str) -> bool:
    """Checks the file's first bytes, so a renamed text file is not accepted."""
    if extension in (".jpg", ".jpeg"):
        return content.startswith(b"\xff\xd8\xff")
    if extension == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == ".webp":
        return content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    return False


async def save_event_image(file: UploadFile) -> str:
    """Validate and store the image. Returns a path like 'uploads/abc123.png'."""
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only JPG, PNG or WEBP images are allowed.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Image must be smaller than 2 MB.")
    if not _looks_like_image(content, extension):
        raise HTTPException(status_code=400, detail="That file is not a valid JPG, PNG or WEBP image.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"  # random name, never the user's
    (UPLOAD_DIR / filename).write_bytes(content)
    return f"uploads/{filename}"


def delete_event_image(image_path: str | None) -> None:
    if not image_path:
        return
    # .name keeps only the file name, so a crafted path can't escape the folder
    (UPLOAD_DIR / Path(image_path).name).unlink(missing_ok=True)