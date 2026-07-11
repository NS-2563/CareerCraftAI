from fastapi import APIRouter
from app.resume.services.resume_rewriter import rewrite_resume

router = APIRouter()

@router.post("/rewrite-resume")
def rewrite(data: dict):

    return rewrite_resume(
        data["skills"],
        data["missing_skills"]
    )