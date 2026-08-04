from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateQuestionsRequest(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=255)
    job_role: Optional[str] = Field(default=None, max_length=255)
    skills: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = Field(default="medium", pattern=r"^(easy|medium|hard)$")
    question_count: int = Field(default=5, ge=1, le=20)
    related_job_application_id: Optional[int] = None


class GeneratedQuestion(BaseModel):
    id: str
    question: str
    category: str
    topic: Optional[str] = None
    difficulty: str


class GenerateQuestionsResponse(BaseModel):
    questions: List[GeneratedQuestion]


class EvaluateAnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    answer: str = Field(..., min_length=1, max_length=10000)
    job_title: Optional[str] = Field(default=None, max_length=255)
    difficulty: Optional[str] = Field(default=None, max_length=50)


class AnswerEvaluation(BaseModel):
    model_config = {"protected_namespaces": ()}
    score: int = Field(..., ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    model_answer_notes: Optional[str] = None


class EvaluateAnswerResponse(BaseModel):
    evaluation: AnswerEvaluation
    evaluation_failed: bool = False


class CreateSessionRequest(BaseModel):
    job_title: Optional[str] = Field(default=None, max_length=255)
    skills: Optional[List[str]] = None
    difficulty: Optional[str] = Field(default=None, max_length=50)
    question_count: int = Field(default=5, ge=1, le=50)
    questions: List[GeneratedQuestion] = Field(default_factory=list)
    related_job_application_id: Optional[int] = None


class UpdateSessionRequest(BaseModel):
    answers: Optional[List[dict]] = None
    overall_score: Optional[float] = Field(default=None, ge=0, le=100)
    completed_at: Optional[str] = None


class CreateRealInterviewRequest(BaseModel):
    """Retrospective log of a real interview, tied to a specific application.

    Deliberately low-friction — free-text notes, a self-rated confidence, and
    optional notes on the questions asked. No per-question Q&A.
    """
    job_application_id: int
    how_it_went: str = Field(..., min_length=1, max_length=5000)
    self_rated_confidence: float = Field(..., ge=0, le=100)
    questions_asked: Optional[str] = Field(default=None, max_length=5000)


class SessionListItem(BaseModel):
    id: int
    session_type: str = "practice"
    job_title: Optional[str] = None
    difficulty: Optional[str] = None
    question_count: int
    overall_score: Optional[float] = None
    self_rated_confidence: Optional[float] = None
    related_job_application_id: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None


class SessionDetail(BaseModel):
    id: int
    session_type: str = "practice"
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    skills: Optional[List[str]] = None
    difficulty: Optional[str] = None
    question_count: int
    questions: List[GeneratedQuestion] = Field(default_factory=list)
    answers: Optional[List[dict]] = None
    overall_score: Optional[float] = None
    how_it_went: Optional[str] = None
    self_rated_confidence: Optional[float] = None
    questions_asked: Optional[str] = None
    related_job_application_id: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None


class PaginatedSessions(BaseModel):
    items: List[SessionListItem]
    pagination: dict


class ProgressOverview(BaseModel):
    total_sessions: int = 0
    average_score: Optional[float] = None
    trend: str = "not_enough_data"


class ProgressByRoleItem(BaseModel):
    job_role_normalized: str
    job_role: Optional[str] = None
    session_count: int = 0
    average_score: Optional[float] = None
    last_practiced_at: Optional[str] = None
    trend: str = "not_enough_data"


class ProgressByCategoryItem(BaseModel):
    category: str
    question_count: int = 0
    average_score: Optional[float] = None


class ProgressResponse(BaseModel):
    overview: ProgressOverview
    by_role: List[ProgressByRoleItem]
    by_category: List[ProgressByCategoryItem]
