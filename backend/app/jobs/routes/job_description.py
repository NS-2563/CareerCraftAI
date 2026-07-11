from fastapi import APIRouter, UploadFile, File
import os

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-jd")
async def upload_jd(file: UploadFile = File(...)):

    file_path = os.path.join(
        UPLOAD_DIR,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    with open(file_path, "r", encoding="utf-8") as f:
        jd_text = f.read()

    return {
        "filename": file.filename,
        "characters": len(jd_text),
        "preview": jd_text[:500]
    }