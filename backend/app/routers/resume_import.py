from fastapi import APIRouter, Depends, status, UploadFile, File
from sqlalchemy.orm import Session
import os
import logging

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.utils.exceptions import ValidationException
from app.utils.upload import save_upload, MAX_UPLOAD_SIZE
from app.resume.services.pdf_parser import extract_text_from_pdf
from app.resume.services.resume_pipeline import parse_resume_full

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resume/import", tags=["Resume Import"])


@router.post("/parse")
async def parse_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Parse a PDF resume without persisting it.

    Runs the full pipeline (section detection → deterministic → AI enrichment)
    and returns the parsed data for frontend review. Does NOT create a DB record.

    The response contains:
      - parsed_data: camelCase resume data compatible with ResumeContext
      - source_meta: per-section provenance metadata (UI-only)
      - resume_name: suggested name based on filename
      - ai_used: whether AI enrichment was attempted
    """
    content = await file.read()

    try:
        file_path = save_upload(content, file.filename or "resume.pdf")
    except ValueError as e:
        raise ValidationException(str(e))

    try:
        extracted_text = extract_text_from_pdf(file_path)
    except Exception as e:
        logger.error("PDF parsing failed for file %s: %s", file.filename, str(e))
        raise ValidationException("Could not parse the PDF file. Ensure it is a valid PDF.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if not extracted_text or not extracted_text.strip():
        raise ValidationException("No extractable text found in the PDF. The file may be a scanned image.")

    filename_stem = os.path.splitext(file.filename or "resume.pdf")[0]
    resume_name = f"Imported - {filename_stem}"

    pipeline_result = parse_resume_full(
        raw_text=extracted_text,
        resume_name=resume_name,
        use_ai=True,
    )

    parsed_data = pipeline_result.get("parsed_data", {})
    source_meta = pipeline_result.get("source_meta", {})
    ai_used = pipeline_result.get("ai_used", False)

    logger.info(
        "IMPORT PARSE user_id=%s filename=%s ai=%s sections=%d",
        current_user.id, file.filename, ai_used, len(source_meta),
    )

    return {
        "parsed_data": parsed_data,
        "source_meta": source_meta,
        "resume_name": resume_name,
        "ai_used": ai_used,
    }
