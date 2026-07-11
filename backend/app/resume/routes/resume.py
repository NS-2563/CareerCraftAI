from fastapi import APIRouter, UploadFile, File
from app.resume.services.pdf_parser import extract_text_from_pdf
from app.resume.services.skill_extractor import extract_skills
from app.resume.services.skill_gap import analyze_skill_gap
from app.resume.services.resume_analyzer import check_resume_completeness
from app.resume.services.ats_score import calculate_ats_score
from app.career.services.suggestions import generate_suggestions
from app.career.services.career_readiness import calculate_career_readiness
from app.career.services.learning_path import generate_learning_path
from app.career.services.employability import predict_employability
from app.jobs.services.job_recommender import recommend_jobs
import os

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    extracted_text = extract_text_from_pdf(file_path)

    skills = extract_skills(extracted_text)
    role = "Software Developer"
    gap_report = analyze_skill_gap(
    skills,
    role
)
    job_recommendations = recommend_jobs(skills)
    
    resume_report = check_resume_completeness(
    extracted_text
)
    ats_score = calculate_ats_score(
        gap_report["match_percentage"],
        resume_report["completeness_score"]
    )

    suggestions = generate_suggestions(
    gap_report["missing_skills"],
    resume_report["sections_found"]
    )

    learning_path = generate_learning_path(
    gap_report["missing_skills"]
    )

    readiness_report = calculate_career_readiness(
    ats_score,
    gap_report["match_percentage"],
    resume_report["sections_found"]
    )

    employability = predict_employability(
    ats_score,
    len(skills),
    resume_report["completeness_score"]
    )

    return {
        "filename": file.filename,
        "skills_found": skills,
        "skill_gap_report": gap_report,
        "resume_analysis": resume_report,
        "ats_score": ats_score,
        "suggestions": suggestions,
        "career_readiness": readiness_report,
        "learning_path": learning_path,
        "employability_prediction": employability,
        "job_recommendations": job_recommendations
    }