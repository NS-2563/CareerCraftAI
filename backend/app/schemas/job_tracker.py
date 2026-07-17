from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    WISHLIST = "Wishlist"
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class JobApplicationBase(BaseModel):
    company: str
    job_title: str
    location: Optional[str] = None

    status: JobStatus = JobStatus.WISHLIST

    source: Optional[str] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None

    applied_date: Optional[date] = None
    deadline: Optional[date] = None


class JobApplicationCreate(JobApplicationBase):
    pass


class JobApplicationUpdate(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None

    status: Optional[JobStatus] = None

    source: Optional[str] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None

    applied_date: Optional[date] = None
    deadline: Optional[date] = None


class JobApplicationResponse(JobApplicationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class JobStatsResponse(BaseModel):
    total_applications: int
    wishlist: int
    applied: int
    interview: int
    offer: int
    accepted: int
    rejected: int
    withdrawn: int

