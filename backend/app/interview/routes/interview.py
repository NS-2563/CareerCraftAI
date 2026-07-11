from fastapi import APIRouter
router = APIRouter()
from app.interview.services.interview_generator import generate_questions

@router.post("/generate-interview")
def interview(data: dict):

    print("Received:", data)

    skills = data["skills"]

    questions = generate_questions(skills)

    return {"questions": questions}