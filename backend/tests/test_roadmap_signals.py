"""Tests for Career Coach roadmap context enrichment with real user signals.

Covers:
- build_context still works with no db/user_id (new-user case)
- build_context omits signal blocks when there is no real data
- build_context includes the skill-gap block when JD matches exist
- build_context includes the weakest-interview-category block when practice data exists
- generate_career_report still succeeds with no signals present
- generate_career_report includes the real signals in the prompt when present
"""

import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
# Import EVERY model so create_all resolves all foreign keys/relationships.
from app.models.user import User  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.career_report import CareerReport  # noqa: F401
from app.models.job_application import JobApplication  # noqa: F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: F401
from app.models.cover_letter import CoverLetter  # noqa: F401
from app.models.jd_match_result import JDMatchResult  # noqa: F401
from app.communication.models import CommunicationMessage, CommunicationSuggestion  # noqa: F401
from app.interview_prep.models import InterviewSession  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    e = create_engine("sqlite://", connect_args={"check_same_thread": False})
    @event.listens_for(e, "connect")
    def _set_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=OFF;")
        cursor.close()

    Base.metadata.create_all(bind=e)
    return e


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, email="test@test.com", username="testuser", password="Test1234!"):
    from app.dependencies import get_password_hash
    from app.models.user import User
    u = User(email=email, username=username,
             hashed_password=get_password_hash(password), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_job(db, user_id, company="Acme", job_title="Engineer"):
    from app.models.job_application import JobApplication
    from app.schemas.job_tracker import JobStatus
    j = JobApplication(
        user_id=user_id, company=company, job_title=job_title,
        status=JobStatus("Applied"),
        job_description="Looking for a Python developer with FastAPI.",
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def _seed_match(db, user_id, missing_skill_names, job=None):
    """Create a stored JDMatchResult row with the given missing skills."""
    from app.models.jd_match_result import JDMatchResult
    items = [{"name": name, "in_jd": True, "in_resume": False} for name in missing_skill_names]
    r = JDMatchResult(
        user_id=user_id,
        job_application_id=job.id if job is not None else None,
        resume_id=None,
        match_score=80.0,
        matched_skills=json.dumps([]),
        missing_skills=json.dumps(items),
        used_ai=False,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _seed_interview_sessions(db, user_id):
    """Seed 2 scored sessions where Behavioral is the weakest category."""
    from app.interview_prep.models import InterviewSession

    def make_session(job_title, answers_scores):
        questions = [
            {"id": "q1", "question": "Tech?", "category": "Technical", "difficulty": "medium"},
            {"id": "q2", "question": "Behave?", "category": "Behavioral", "difficulty": "easy"},
            {"id": "q3", "question": "HR?", "category": "HR", "difficulty": "easy"},
        ]
        answers = []
        for i, (qid, score) in enumerate(answers_scores.items()):
            answers.append({
                "questionId": qid,
                "answer": f"answer {i}",
                "skipped": False,
                "evaluation": {"score": score, "evaluation_failed": False},
            })
        sess = InterviewSession(
            user_id=user_id,
            job_title=job_title,
            job_role_normalized=job_title.lower(),
            overall_score=60.0,
            question_count=3,
            questions=json.dumps(questions),
            answers=json.dumps(answers),
            created_at=datetime.utcnow() - timedelta(hours=1),
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow(),
        )
        db.add(sess)

    # Behavioral consistently low (40), Technical high (80), HR mid (60).
    make_session("Backend Dev", {"q1": 80, "q2": 40, "q3": 60})
    make_session("Frontend Dev", {"q1": 78, "q2": 38, "q3": 62})
    db.commit()


VALID_REPORT = {
    "career_goal": "Backend Engineer",
    "readiness_score": 70,
    "readiness_status": "Good",
    "best_match": "Software Engineer",
    "career_summary": "Solid foundation.",
    "strengths": ["Python"],
    "weaknesses": ["Docker"],
    "career_paths": [{"title": "Backend", "reason": "Fit", "difficulty": "Intermediate", "future_demand": "High"}],
    "skill_gap": {"existing_skills": ["Python"], "missing_skills": ["Docker"], "priority": ["Docker"]},
    "roadmap": [{"stage": "Foundation", "topics": ["Python"], "projects": []}],
    "action_plan": {"next_week": [], "next_month": [], "next_6_months": []},
    "resources": [{"title": "Docs", "type": "Course", "description": "Read docs"}],
}


# ---------------------------------------------------------------------------
# build_context: presence/absence of signals
# ---------------------------------------------------------------------------

class TestBuildContextSignals:

    def test_works_without_db_or_user_id(self):
        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={"goal": "Backend", "skills": ["Python"]})
        assert "You are CareerCraft AI." in ctx
        assert "Application Module:" in ctx
        assert "Backend" in ctx
        assert "Real User Signals" not in ctx

    def test_no_signal_blocks_without_data(self, db_session):
        user = _create_user(db_session)
        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={}, db=db_session, user_id=user.id)
        assert "Real User Signals" in ctx
        assert "not enough saved JD matches yet (skipped)" in ctx
        assert "not enough practice data yet (skipped)" in ctx
        assert "Docker" not in ctx

    def test_skill_gap_block_included_when_matches_exist(self, db_session):
        user = _create_user(db_session)
        jobs = [_create_job(db_session, user.id, f"Company{i}") for i in range(3)]
        _seed_match(db_session, user.id, ["Docker"], jobs[0])
        _seed_match(db_session, user.id, ["Docker"], jobs[1])
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"], jobs[2])

        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={}, db=db_session, user_id=user.id)
        assert "Skill gaps from the user's own saved JD matches:" in ctx
        assert "Docker: required in 3 of 3 applications, missing from resume" in ctx
        assert "Kubernetes: required in 1 of 3 applications, missing from resume" in ctx

    def test_weakest_interview_block_included_when_sessions_exist(self, db_session):
        user = _create_user(db_session)
        _seed_interview_sessions(db_session, user.id)

        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={}, db=db_session, user_id=user.id)
        assert "Weakest interview category" in ctx
        assert "Behavioral" in ctx

    def test_weakest_interview_block_skipped_with_one_session(self, db_session):
        user = _create_user(db_session)
        from app.interview_prep.models import InterviewSession
        import json as _json
        sess = InterviewSession(
            user_id=user.id, job_title="Dev", job_role_normalized="dev",
            overall_score=50.0, question_count=2,
            questions=_json.dumps([{"id": "q1", "question": "T", "category": "Technical"}]),
            answers=_json.dumps([{"questionId": "q1", "answer": "a", "skipped": False,
                                  "evaluation": {"score": 40, "evaluation_failed": False}}]),
        )
        db_session.add(sess)
        db_session.commit()

        from app.ai.context_builder import build_context
        ctx = build_context(module="Career Coach", user_data={}, db=db_session, user_id=user.id)
        assert "not enough practice data yet (skipped)" in ctx
        assert "Weakest interview category" not in ctx


# ---------------------------------------------------------------------------
# generate_career_report: new-user fallback + signals passed to the model
# ---------------------------------------------------------------------------

class TestGenerateCareerReportSignals:

    def test_new_user_without_signals_still_generates_report(self, db_session, monkeypatch):
        user = _create_user(db_session)

        captured = {}

        def fake_generate_json(prompt=None, schema=None):
            captured["prompt"] = prompt
            return {"success": True, "data": dict(VALID_REPORT)}

        monkeypatch.setattr(
            "app.career.services.roadmap_service.generate_json",
            fake_generate_json,
        )

        from app.career.services.roadmap_service import generate_career_report
        result = generate_career_report(
            {"goal": "Backend Engineer", "skills": "Python"},
            db=db_session,
            user_id=user.id,
        )

        assert result.get("success") is True
        assert result.get("source") == "ai"
        prompt = captured["prompt"]
        # New user: signal block present but gracefully skipped (no data),
        # and the resume-based fallback instructions are still present.
        assert "Real User Signals" in prompt
        assert "not enough saved JD matches yet (skipped)" in prompt
        assert "not enough practice data yet (skipped)" in prompt
        assert "Skill Gap:" in prompt
        assert "fall back to the resume-based approach" in prompt

    def test_signals_included_in_prompt_when_present(self, db_session, monkeypatch):
        user = _create_user(db_session)
        jobs = [_create_job(db_session, user.id, f"Company{i}") for i in range(3)]
        _seed_match(db_session, user.id, ["Docker"], jobs[0])
        _seed_match(db_session, user.id, ["Docker"], jobs[1])
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"], jobs[2])
        _seed_interview_sessions(db_session, user.id)

        captured = {}

        def fake_generate_json(prompt=None, schema=None):
            captured["prompt"] = prompt
            return {"success": True, "data": dict(VALID_REPORT)}

        monkeypatch.setattr(
            "app.career.services.roadmap_service.generate_json",
            fake_generate_json,
        )

        from app.career.services.roadmap_service import generate_career_report
        result = generate_career_report(
            {"goal": "Backend Engineer", "skills": "Python"},
            db=db_session,
            user_id=user.id,
        )

        assert result.get("success") is True
        prompt = captured["prompt"]
        # Real signals are present in the context passed to the model.
        assert "Real User Signals" in prompt
        assert "Skill gaps from the user's own saved JD matches:" in prompt
        assert "Docker: required in 3 of 3 applications, missing from resume" in prompt
        assert "Weakest interview category" in prompt
        assert "Behavioral" in prompt
        # The model is told to ground recommendations in them.
        assert "REAL USER SIGNALS" in prompt

    def test_fallback_report_still_generated_when_ai_fails(self, db_session):
        user = _create_user(db_session)
        _create_job(db_session, user.id)

        from app.career.services.roadmap_service import generate_career_report
        result = generate_career_report(
            {"goal": "Backend Engineer", "skills": "Python"},
            db=db_session,
            user_id=user.id,
        )

        # AI provider unavailable in test env -> deterministic fallback.
        assert result.get("success") is True
        assert result.get("source") in ("ai", "fallback")
        assert "skill_gap" in result.get("data", {})
