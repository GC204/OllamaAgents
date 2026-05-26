"""File ingestion endpoint."""
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException

from src.config import get_settings, ensure_dirs
from src.ingestion import ingest_file

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv"}


@router.post("/ingest")
async def ingest(upload: UploadFile = File(...)):
    ensure_dirs(get_settings())
    settings = get_settings()
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    safe_name = f"{uuid.uuid4().hex}_{upload.filename}"
    path = Path(settings.upload_dir) / safe_name
    try:
        contents = await upload.read()
        path.write_bytes(contents)
        result = ingest_file(path, filename=upload.filename)
        return result
    except Exception as e:
        if path.exists():
            path.unlink(missing_ok=True)
        raise HTTPException(500, detail=str(e))
