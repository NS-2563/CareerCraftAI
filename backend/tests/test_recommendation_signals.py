"""Tests for deterministic signal scoring of Career Coach priority recommendations.

Covers:
- new user: only the roadmap-overlap signal is evaluable, everything else excluded
- JD evidence fires from stored match results and is excluded below the sample size
- resume-analysis signal reads recommended skill names
- weakest-interview-category signal matches practice data
- unevaluable signals are excluded from BOTH counts (never "0 of N")
- deterministic output: same input, same counts
- generate_career_report attaches enriched priority in the AI branch
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


def _seed_resume_analysis(db, user_id, recommended=("Docker",)):
    from app.models.resume_analysis import ResumeAnalysis
    from app.models.resume import Resume
    resume = Resume(user_id=user_id, name="Resume A", completed=False)
    db.add(resume)
    db.flush()
    analysis_json = {
        "skill_suggestions": {
            "current_strengths": ["Python"],
            "gaps": [],
            "recommended": [{"skill": name, "reason": "Jobs ask for it"} for name in recommended],
        },
        "deep_analysis": {
            "ai_analysis": {
                "skill_suggestions": {
                    "recommended": [{"skill": "Kubernetes", "reason": ""}],
                }
            }
        },
    }
    record = ResumeAnalysis(
        user_id=user_id,
        resume_id=resume.id,
        resume_version=1,
        source="full",
        analysis_json=analysis_json,
        scores_json=None,
        is_stale=0,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


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

    make_session("Backend Dev", {"q1": 80, "q2": 40, "q3": 60})
    make_session("Frontend Dev", {"q1": 78, "q2": 38, "q3": 62})
    db.commit()


def _report(priority=("Docker",), roadmap_topics=("Python",), missing_skills=()):
    return {
        "career_goal": "Backend Engineer",
        "readiness_score": 70,
        "readiness_status": "Good",
        "skill_gap": {
            "existing_skills": ["Python"],
            "missing_skills": list(missing_skills),
            "priority": list(priority),
        },
        "roadmap": [{"stage": "Foundation", "topics": list(roadmap_topics), "projects": []}],
        "action_plan": {"next_week": [], "next_month": [], "next_6_months": []},
        "resources": [],
    }


# ---------------------------------------------------------------------------
# Enrichment behaviour
# ---------------------------------------------------------------------------

class TestEnrichment:

    def test_new_user_only_roadmap_signal_evaluable(self, db_session):
        user = _create_user(db_session)
        from app.career.services.recommendation_signals import enrich_priority_recommendations

        result = enrich_priority_recommendations(
            _report(priority=["Docker"], roadmap_topics=["Python"]),
            db_session,
            user.id,
        )

        assert len(result) == 1
        entry = result[0]
        assert entry["skill"] == "Docker"
        assert entry["total_possible_signals"] == 1
        assert entry["supported_signals"] == 0
        assert entry["reasons"] == []

    def test_new_user_roadmap_reinforcement_fires(self, db_session):
        user = _create_user(db_session)
        from app.career.services.recommendation_signals import enrich_priority_recommendations

        result = enrich_priority_recommendations(
            _report(priority=["Docker"], roadmap_topics=["Python", "Docker"]),
            db_session,
            user.id,
        )

        entry = result[0]
        assert entry["total_possible_signals"] == 1
        assert entry["supported_signals"] == 1
        assert "Reinforced in your learning roadmap" in entry["reasons"]

    def test_jd_signal_fires_and_roadmap_stays_honest(self, db_session):
        user = _create_user(db_session)
        jobs = [_create_job(db_session, user.id, f"Company{i}") for i in range(3)]
        _seed_match(db_session, user.id, ["Docker"], jobs[0])
        _seed_match(db_session, user.id, ["Docker"], jobs[1])
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"], jobs[2])

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        result = enrich_priority_recommendations(
            _report(priority=["Docker"], roadmap_topics=["Python"]),
            db_session,
            user.id,
        )

        entry = result[0]
        assert entry["total_possible_signals"] == 2
        assert entry["supported_signals"] == 1
        assert any("Missing in 3 of 3 saved job matches" in r for r in entry["reasons"])

    def test_jd_signal_unevaluable_below_sample_size(self, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        _seed_match(db_session, user.id, ["Docker"], job)

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        result = enrich_priority_recommendations(
            _report(priority=["Docker"], roadmap_topics=["Python"]),
            db_session,
            user.id,
        )

        entry = result[0]
        assert entry["total_possible_signals"] == 1
        assert entry["supported_signals"] == 0

    def test_resume_analysis_signal_fires(self, db_session):
        user = _create_user(db_session)
        _seed_resume_analysis(db_session, user.id, recommended=("Docker",))

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        result = enrich_priority_recommendations(
            _report(priority=["Docker"], roadmap_topics=["Python"]),
            db_session,
            user.id,
        )

        entry = result[0]
        assert entry["total_possible_signals"] == 2
        assert entry["supported_signals"] == 1
        assert any("Flagged as a skill to add in your resume analysis" in r for r in entry["reasons"])

    def test_interview_signal_fires_for_weak_category(self, db_session):
        user = _create_user(db_session)
        _seed_interview_sessions(db_session, user.id)

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        result = enrich_priority_recommendations(
            _report(priority=["Behavioral"], roadmap_topics=["Python"]),
            db_session,
            user.id,
        )

        entry = result[0]
        assert entry["total_possible_signals"] == 2
        assert entry["supported_signals"] == 1
        assert any(
            "Targets your weakest interview area (Behavioral" in r
            for r in entry["reasons"]
        )

    def test_interview_signal_unevaluable_without_sessions(self, db_session):
        user = _create_user(db_session)

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        result = enrich_priority_recommendations(
            _report(priority=["Behavioral"], roadmap_topics=["Python"]),
            db_session,
            user.id,
        )

        entry = result[0]
        assert entry["total_possible_signals"] == 1
        assert entry["supported_signals"] == 0

    def test_all_sources_present_all_evaluable(self, db_session):
        user = _create_user(db_session)
        jobs = [_create_job(db_session, user.id, f"Company{i}") for i in range(3)]
        _seed_match(db_session, user.id, ["Docker"], jobs[0])
        _seed_match(db_session, user.id, ["Docker"], jobs[1])
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"], jobs[2])
        _seed_resume_analysis(db_session, user.id, recommended=("Docker",))
        _seed_interview_sessions(db_session, user.id)

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        result = enrich_priority_recommendations(
            _report(priority=["Docker"], roadmap_topics=["Docker"], missing_skills=["Docker"]),
            db_session,
            user.id,
        )

        entry = result[0]
        # JD + resume + roadmap fire; interview category does not match "Docker".
        assert entry["total_possible_signals"] == 4
        assert entry["supported_signals"] == 3
        assert len(entry["reasons"]) == 3

    def test_never_fabricates_total_beyond_evaluable_signals(self, db_session):
        user = _create_user(db_session)

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        result = enrich_priority_recommendations(
            _report(priority=["Docker"], roadmap_topics=["Python"]),
            db_session,
            user.id,
        )

        entry = result[0]
        assert entry["total_possible_signals"] <= 4
        assert entry["supported_signals"] <= entry["total_possible_signals"]

    def test_deterministic_same_input_same_output(self, db_session):
        user = _create_user(db_session)
        jobs = [_create_job(db_session, user.id, f"Company{i}") for i in range(3)]
        _seed_match(db_session, user.id, ["Docker"], jobs[0])
        _seed_match(db_session, user.id, ["Docker"], jobs[1])
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"], jobs[2])

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        report = _report(priority=["Docker", "Kubernetes"], roadmap_topics=["Python", "Docker"])
        first = enrich_priority_recommendations(report, db_session, user.id)
        second = enrich_priority_recommendations(report, db_session, user.id)
        assert first == second

    def test_dict_priority_items_supported(self, db_session):
        user = _create_user(db_session)

        from app.career.services.recommendation_signals import enrich_priority_recommendations
        report = _report(priority=[], roadmap_topics=["Python"])
        report["skill_gap"]["priority"] = [{"skill": "Docker", "note": "AI entry"}]
        result = enrich_priority_recommendations(report, db_session, user.id)
        assert result[0]["skill"] == "Docker"
        assert result[0]["total_possible_signals"] == 1


# ---------------------------------------------------------------------------
# Wiring into generate_career_report
# ---------------------------------------------------------------------------

class TestCareerReportWiring:

    def test_ai_branch_priority_is_enriched(self, db_session, monkeypatch):
        user = _create_user(db_session)
        jobs = [_create_job(db_session, user.id, f"Company{i}") for i in range(3)]
        _seed_match(db_session, user.id, ["Docker"], jobs[0])
        _seed_match(db_session, user.id, ["Docker"], jobs[1])
        _seed_match(db_session, user.id, ["Docker", "Kubernetes"], jobs[2])

        def fake_generate_json(prompt=None, schema=None):
            return {"success": True, "data": _report(
                priority=["Docker"], roadmap_topics=["Python", "Docker"],
                missing_skills=["Docker"],
            )}

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
        priority = result["data"]["skill_gap"]["priority"]
        assert isinstance(priority, list) and len(priority) == 1
        entry = priority[0]
        assert entry["skill"] == "Docker"
        assert entry["total_possible_signals"] == 2
        assert entry["supported_signals"] == 2
        assert any("Missing in 3 of 3 saved job matches" in r for r in entry["reasons"])
        assert any("Reinforced in your learning roadmap" in r for r in entry["reasons"])
