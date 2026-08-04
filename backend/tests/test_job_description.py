"""Tests for the completed Job Description → JD Match pipeline (Phase 12).

Covers:
- create_job persists job_description + resume_id (previously dropped)
- create_job with empty JD leaves the column unchanged (NULL)
- PUT /api/jobs/{id} persists job_description
- JOB_DESCRIPTION_ADDED / JOB_DESCRIPTION_UPDATED activity events
- Improved validation message when analyze-saved hits a JD-less application
- Full pipeline: Job → Save JD → Resume Match → JD Match Result → Skill Gap
"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.job_application import JobApplication  # noqa: F401
from app.models.jd_match_result import JDMatchResult  # noqa: F401
from app.models.career_report import CareerReport  # noqa: F401
from app.activity.models import ActivityEvent  # noqa: F401
from app.activity.constants import EventType  # noqa: F401

SAMPLE_JD_TEXT = (
    "Senior Software Engineer\n\n"
    "We are looking for a Senior Software Engineer with experience in "
    "Python, JavaScript, and React. Strong knowledge of PostgreSQL, Docker, "
    "and AWS. Experience with FastAPI is a plus.\n"
)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _create_user(db, email="jd@test.com", username="jduser"):
    from app.dependencies import get_password_hash
    u = User(email=email, username=username,
             hashed_password=get_password_hash("Test1234!"), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_resume(db, user_id):
    r = Resume(
        user_id=user_id,
        name="Test Resume",
        personal=json.dumps({"first_name": "John", "last_name": "Doe"}),
        summary="Senior software engineer with 6 years of experience.",
        experience=json.dumps([
            {"company": "TechCorp", "position": "Senior Engineer",
             "start_date": "2020-03", "end_date": "2024-12",
             "description": "Python, FastAPI, PostgreSQL, AWS work."},
        ]),
        skills=json.dumps([
            {"name": "Python", "category": "Programming Languages"},
            {"name": "FastAPI", "category": "Frameworks"},
            {"name": "PostgreSQL", "category": "Databases"},
            {"name": "AWS", "category": "Cloud Technologies"},
        ]),
        education=json.dumps([]),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _auth(user):
    from app.dependencies import create_access_token
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _jd_events(db, user_id, event_type):
    return db.query(ActivityEvent).filter(
        ActivityEvent.user_id == user_id,
        ActivityEvent.event_type == event_type,
    ).all()


# ---------------------------------------------------------------------------
# Create Job persists job_description + resume_id
# ---------------------------------------------------------------------------

class TestCreateJobPersistsJd:

    def test_create_persists_job_description_and_resume_id(self, client, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        headers = _auth(user)

        r = client.post("/api/jobs", headers=headers, json={
            "company": "Acme",
            "job_title": "Engineer",
            "job_description": SAMPLE_JD_TEXT,
            "resume_id": resume.id,
        })
        assert r.status_code == 201
        body = r.json()
        assert body["job_description"] == SAMPLE_JD_TEXT
        assert body["resume_id"] == resume.id

        row = db_session.query(JobApplication).filter(
            JobApplication.user_id == user.id
        ).one()
        assert row.job_description == SAMPLE_JD_TEXT
        assert row.resume_id == resume.id

    def test_create_without_jd_leaves_null(self, client, db_session):
        user = _create_user(db_session)
        headers = _auth(user)

        r = client.post("/api/jobs", headers=headers, json={
            "company": "Acme",
            "job_title": "Engineer",
        })
        assert r.status_code == 201

        row = db_session.query(JobApplication).filter(
            JobApplication.user_id == user.id
        ).one()
        assert row.job_description is None

    def test_create_with_jd_logs_added_activity(self, client, db_session):
        user = _create_user(db_session)
        headers = _auth(user)

        r = client.post("/api/jobs", headers=headers, json={
            "company": "Acme",
            "job_title": "Engineer",
            "job_description": "Python developer",
        })
        assert r.status_code == 201
        job_id = r.json()["id"]

        events = _jd_events(db_session, user.id, EventType.JOB_DESCRIPTION_ADDED)
        assert len(events) == 1
        assert events[0].related_entity_id == job_id

    def test_create_without_jd_logs_no_added_activity(self, client, db_session):
        user = _create_user(db_session)
        headers = _auth(user)
        client.post("/api/jobs", headers=headers, json={
            "company": "Acme",
            "job_title": "Engineer",
        })
        assert _jd_events(db_session, user.id, EventType.JOB_DESCRIPTION_ADDED) == []


# ---------------------------------------------------------------------------
# Update Job persists job_description
# ---------------------------------------------------------------------------

class TestUpdateJobJd:

    def _create_job_row(self, db, user_id, jd=None):
        j = JobApplication(
            user_id=user_id, company="Acme", job_title="Engineer",
            job_description=jd,
        )
        db.add(j)
        db.commit()
        db.refresh(j)
        return j

    def test_update_persists_job_description(self, client, db_session):
        user = _create_user(db_session)
        job = self._create_job_row(db_session, user.id)
        headers = _auth(user)

        r = client.put(f"/api/jobs/{job.id}", headers=headers, json={
            "job_description": SAMPLE_JD_TEXT,
        })
        assert r.status_code == 200
        assert r.json()["job_description"] == SAMPLE_JD_TEXT

        db_session.refresh(job)
        assert job.job_description == SAMPLE_JD_TEXT

    def test_update_adds_activity_when_jd_was_empty(self, client, db_session):
        user = _create_user(db_session)
        job = self._create_job_row(db_session, user.id)
        headers = _auth(user)

        client.put(f"/api/jobs/{job.id}", headers=headers, json={
            "job_description": "Python developer",
        })

        added = _jd_events(db_session, user.id, EventType.JOB_DESCRIPTION_ADDED)
        updated = _jd_events(db_session, user.id, EventType.JOB_DESCRIPTION_UPDATED)
        assert len(added) == 1
        assert len(updated) == 0

    def test_update_logs_updated_when_jd_changed(self, client, db_session):
        user = _create_user(db_session)
        job = self._create_job_row(db_session, user.id, jd="Old description")
        headers = _auth(user)

        client.put(f"/api/jobs/{job.id}", headers=headers, json={
            "job_description": "New, better description",
        })

        added = _jd_events(db_session, user.id, EventType.JOB_DESCRIPTION_ADDED)
        updated = _jd_events(db_session, user.id, EventType.JOB_DESCRIPTION_UPDATED)
        assert len(added) == 0
        assert len(updated) == 1


# ---------------------------------------------------------------------------
# Improved validation message on analyze-saved
# ---------------------------------------------------------------------------

class TestAnalyzeSavedMessage:

    def test_no_jd_returns_helpful_message(self, client, db_session):
        user = _create_user(db_session)
        job = JobApplication(user_id=user.id, company="NoJD", job_title="NoJD Title")
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        headers = _auth(user)

        r = client.post(f"/api/jd-match/analyze-saved/{job.id}", headers=headers)
        assert r.status_code == 422
        text = r.text.lower()
        assert "no saved job description" in text
        assert "save a job description" in text

    def test_other_job_404_unchanged(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = JobApplication(user_id=owner.id, company="OwnerCo", job_title="T")
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        r = client.post(
            f"/api/jd-match/analyze-saved/{job.id}",
            headers=_auth(attacker),
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Full pipeline: Job → Save JD → Resume Match → Result → Skill Gap
# ---------------------------------------------------------------------------

class TestFullPipeline:

    def test_complete_pipeline(self, client, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        headers = _auth(user)

        job = client.post("/api/jobs", headers=headers, json={
            "company": "TechCorp",
            "job_title": "Senior Engineer",
            "job_description": SAMPLE_JD_TEXT,
            "resume_id": resume.id,
        }).json()

        # Resume Match against the saved JD.
        r = client.post(f"/api/jd-match/analyze-saved/{job['id']}", headers=headers)
        assert r.status_code == 200
        match = r.json()
        assert match["overall_match_score"] >= 0

        # JD Match result is stored.
        stored = db_session.query(JDMatchResult).filter(
            JDMatchResult.job_application_id == job["id"],
            JDMatchResult.user_id == user.id,
        ).all()
        assert len(stored) == 1

        latest = client.get(f"/api/jd-match/results/{job['id']}", headers=headers)
        assert latest.status_code == 200
        assert latest.json()["match_score"] == match["overall_match_score"]

        # Career Coach Skill Gap consumes the match history.
        from app.career.services.analytics_service import get_skill_gap_summary
        summary = get_skill_gap_summary(db_session, user.id)
        assert summary["total_applications"] == 1

    def test_skill_gap_has_data_after_three_matches(self, client, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        headers = _auth(user)

        for i in range(3):
            job = client.post("/api/jobs", headers=headers, json={
                "company": f"Co{i}",
                "job_title": "Engineer",
                "job_description": SAMPLE_JD_TEXT,
                "resume_id": resume.id,
            }).json()
            r = client.post(f"/api/jd-match/analyze-saved/{job['id']}", headers=headers)
            assert r.status_code == 200

        from app.career.services.analytics_service import get_skill_gap_summary
        summary = get_skill_gap_summary(db_session, user.id)
        assert summary["total_applications"] == 3
        assert summary["has_data"] is True
