from fastapi import APIRouter
from app.interview.services.interview_evaluator import evaluate_answer

router = APIRouter()

@router.post("/evaluate-answer")
def evaluate(data: dict):

    return evaluate_answer(
        data["answer"]
    )