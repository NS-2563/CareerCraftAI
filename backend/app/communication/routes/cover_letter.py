from fastapi import APIRouter
from app.communication.services.cover_letter import generate_cover_letter

router = APIRouter()

@router.post("/cover-letter")
def cover_letter(data: dict):

    letter = generate_cover_letter(
        data["name"],
        data["job_role"],
        data["company"],
        data["skills"]
    )

    return {
        "cover_letter": letter
    }