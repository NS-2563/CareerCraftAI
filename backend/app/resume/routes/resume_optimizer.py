from fastapi import APIRouter
from app.resume.services.resume_optimizer import optimize_resume

router = APIRouter()

@router.post("/optimize-resume")
def optimize(data: dict):

    optimized = optimize_resume(
        data["resume"],
        data["job_role"]
    )

    return {
        "optimized_resume": optimized
    }