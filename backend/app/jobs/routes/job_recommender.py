from fastapi import APIRouter
from app.jobs.services.job_recommender import recommend_jobs

router = APIRouter()

@router.post("/job-recommendations")
def jobs(data: dict):

    return {
        "recommended_jobs": recommend_jobs(
            data["skills"]
        )
    }
