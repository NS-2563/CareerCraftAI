from pydantic import BaseModel, Field
from typing import Optional


class CareerCoachRequest(BaseModel):
    goal: Optional[str] = Field(None, max_length=500)
    skills: Optional[str] = Field(None, max_length=5000)
    experience: Optional[list] = None
    education: Optional[list] = None
    projects: Optional[list] = None
    certifications: Optional[list] = None
