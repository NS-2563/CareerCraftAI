from fastapi import APIRouter
from app.communication.services.cold_email import generate_cold_email

router = APIRouter()

@router.post("/cold-email")
def create_email(data: dict):

    return {
        "email": generate_cold_email(
            data["name"],
            data["role"]
        )
    }