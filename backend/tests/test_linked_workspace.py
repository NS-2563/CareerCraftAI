"""Tests for the per-application linked workspace features.

Covers:
- JDMatchResult persistence when job_application_id is provided
- GET /api/jd-match/results/{job_application_id} (ownership-checked)
- Cover letter job_application_id link (create/update ownership checks)
- Cover letter FK nulls out (SET NULL) when the application is removed
"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dependencies import create_access_token


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


def _create_resume(db, user_id, name="Resume A"):
    from app.models.resume import Resume
    r = Resume(
        user_id=user_id, name=name, completed=True,
        personal=json.dumps({"first_name": "John", "last_name": "Doe"}),
        summary="Senior engineer",
        experience=json.dumps([
            {"company": "TechCorp", "position": "Eng",
             "description": "Python and FastAPI work."},
        ]),
        skills=json.dumps([
            {"name": "Python", "category": "Lang"},
            {"name": "FastAPI", "category": "FW"},
        ]),
        education=json.dumps([]),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _create_job(db, user_id, company="Acme", job_title="Engineer", resume_id=None):
    from app.models.job_application import JobApplication
    from app.schemas.job_tracker import JobStatus
    j = JobApplication(
        user_id=user_id, company=company, job_title=job_title,
        status=JobStatus("Applied"),
        job_description="Looking for a Python developer with FastAPI.",
        resume_id=resume_id,
    )
    db.add(j)
    db.commit()
    db.refresh(j)
    return j


def _auth(user):
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


SAMPLE_RESUME_DATA = {
    "personal": {"first_name": "John", "last_name": "Doe"},
    "summary": "Senior engineer",
    "experience": [
        {"company": "TechCorp", "position": "Eng",
         "description": "Python and FastAPI work."},
    ],
    "education": [],
    "skills": [
        {"name": "Python", "category": "Lang"},
        {"name": "FastAPI", "category": "FW"},
    ],
    "projects": [],
    "certifications": [],
    "languages": [],
}


# ---------------------------------------------------------------------------
# API: JDMatchResult persistence + retrieval
# ---------------------------------------------------------------------------

class TestJDMatchPersistence:

    @pytest.fixture
    def client(self, db_session):
        def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_analyze_persists_result_when_job_application_id_given(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        headers = _auth(user)

        r = client.post("/api/jd-match/analyze", headers=headers, json={
            "jd_text": "Looking for a Python developer with FastAPI.",
            "resume_data": SAMPLE_RESUME_DATA,
            "job_application_id": job.id,
        })
        assert r.status_code == 200
        score = r.json()["overall_match_score"]
        assert score > 0

        from app.models.jd_match_result import JDMatchResult
        stored = db_session.query(JDMatchResult).filter(
            JDMatchResult.job_application_id == job.id,
            JDMatchResult.user_id == user.id,
        ).all()
        assert len(stored) == 1
        assert stored[0].match_score == score
        assert stored[0].used_ai is False
        assert stored[0].resume_id is None

    def test_analyze_without_job_application_is_stateless(self, client, db_session):
        user = _create_user(db_session)
        headers = _auth(user)

        r = client.post("/api/jd-match/analyze", headers=headers, json={
            "jd_text": "Looking for a Python developer with FastAPI.",
            "resume_data": SAMPLE_RESUME_DATA,
        })
        assert r.status_code == 200

        from app.models.jd_match_result import JDMatchResult
        stored = db_session.query(JDMatchResult).filter(
            JDMatchResult.user_id == user.id,
        ).all()
        assert stored == []

    def test_analyze_foreign_application_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job(db_session, owner.id, "OwnerCo")

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = _auth(attacker)

        r = client.post("/api/jd-match/analyze", headers=headers, json={
            "jd_text": "Python developer",
            "resume_data": SAMPLE_RESUME_DATA,
            "job_application_id": job.id,
        })
        assert r.status_code == 404

    def test_analyze_saved_persists_result(self, client, db_session):
        user = _create_user(db_session)
        resume = _create_resume(db_session, user.id)
        job = _create_job(db_session, user.id, resume_id=resume.id)
        headers = _auth(user)

        r = client.post(f"/api/jd-match/analyze-saved/{job.id}", headers=headers)
        assert r.status_code == 200
        score = r.json()["overall_match_score"]
        assert score > 0

        from app.models.jd_match_result import JDMatchResult
        stored = db_session.query(JDMatchResult).filter(
            JDMatchResult.job_application_id == job.id,
        ).all()
        assert len(stored) == 1
        assert stored[0].match_score == score
        assert stored[0].resume_id == resume.id

    def test_get_result_returns_latest(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        headers = _auth(user)

        # Run twice; each run appends a new row, so the latest is the last one.
        scores = []
        for jd in ("Python developer", "FastAPI expert with Docker and AWS"):
            r = client.post("/api/jd-match/analyze", headers=headers, json={
                "jd_text": jd,
                "resume_data": SAMPLE_RESUME_DATA,
                "job_application_id": job.id,
            })
            assert r.status_code == 200
            scores.append(r.json()["overall_match_score"])

        from app.models.jd_match_result import JDMatchResult
        rows = db_session.query(JDMatchResult).filter(
            JDMatchResult.job_application_id == job.id,
        ).order_by(JDMatchResult.id).all()
        assert len(rows) == 2

        r = client.get(f"/api/jd-match/results/{job.id}", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["match_score"] == scores[-1]
        assert data["match_score"] == rows[-1].match_score
        assert data["job_application_id"] == job.id
        assert data["used_ai"] is False

    def test_get_result_requires_auth(self, client):
        r = client.get("/api/jd-match/results/1")
        assert r.status_code == 401

    def test_get_result_foreign_application_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job(db_session, owner.id, "OwnerCo")
        headers = _auth(owner)

        client.post("/api/jd-match/analyze", headers=headers, json={
            "jd_text": "Python developer",
            "resume_data": SAMPLE_RESUME_DATA,
            "job_application_id": job.id,
        })

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        r = client.get(f"/api/jd-match/results/{job.id}", headers=_auth(attacker))
        assert r.status_code == 404

    def test_get_result_none_stored_returns_404(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        r = client.get(f"/api/jd-match/results/{job.id}", headers=_auth(user))
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Cover letter job_application_id link
# ---------------------------------------------------------------------------

class TestCoverLetterLink:

    @pytest.fixture
    def client(self, db_session):
        def _get_db_override():
            yield db_session
        app.dependency_overrides[get_db] = _get_db_override
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()

    def test_create_cover_letter_with_job_application_link(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id)
        headers = _auth(user)

        r = client.post("/api/cover-letter", headers=headers, json={
            "title": "CL for Acme",
            "content": "Dear hiring manager...",
            "job_title": "Engineer",
            "company_name": "Acme",
            "job_application_id": job.id,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["job_application_id"] == job.id

    def test_create_cover_letter_foreign_job_returns_404(self, client, db_session):
        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job = _create_job(db_session, owner.id, "OwnerCo")

        attacker = _create_user(db_session, email="attacker@test.com", username="attacker")
        headers = _auth(attacker)

        r = client.post("/api/cover-letter", headers=headers, json={
            "title": "CL",
            "content": "body",
            "job_application_id": job.id,
        })
        assert r.status_code == 404

    def test_update_cover_letter_foreign_job_returns_404(self, client, db_session):
        user = _create_user(db_session)
        job_owned = _create_job(db_session, user.id, "OwnedCo")

        r = client.post("/api/cover-letter", headers=_auth(user), json={
            "title": "CL", "content": "body",
            "job_application_id": job_owned.id,
        })
        cl_id = r.json()["id"]

        owner = _create_user(db_session, email="owner@test.com", username="owner")
        job_foreign = _create_job(db_session, owner.id, "ForeignCo")

        r = client.put(f"/api/cover-letter/{cl_id}", headers=_auth(user), json={
            "job_application_id": job_foreign.id,
        })
        assert r.status_code == 404

    def test_list_cover_letters_filtered_by_job_application(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id, "Acme")
        other = _create_job(db_session, user.id, "Beta")
        headers = _auth(user)

        client.post("/api/cover-letter", headers=headers, json={
            "title": "For Acme", "content": "body",
            "job_application_id": job.id,
        })
        client.post("/api/cover-letter", headers=headers, json={
            "title": "For Beta", "content": "body",
            "job_application_id": other.id,
        })

        r = client.get(f"/api/cover-letter?job_application_id={job.id}", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["title"] == "For Acme"

    def test_cover_letter_fk_nulls_out_when_application_deleted(self, client, db_session):
        from app.models.job_application import JobApplication

        user = _create_user(db_session)
        job = _create_job(db_session, user.id, "Acme")
        headers = _auth(user)

        r = client.post("/api/cover-letter", headers=headers, json={
            "title": "CL", "content": "body",
            "job_application_id": job.id,
        })
        cl_id = r.json()["id"]
        assert r.json()["job_application_id"] == job.id

        # Delete the job application via the API.
        dr = client.delete(f"/api/jobs/{job.id}", headers=headers)
        assert dr.status_code == 200

        # Cover letter survives; its link is nulled (SET NULL), not cascade-deleted.
        from app.models.cover_letter import CoverLetter
        cl = db_session.query(CoverLetter).filter(CoverLetter.id == cl_id).first()
        assert cl is not None
        assert cl.job_application_id is None

    def test_cover_letter_survives_application_delete_no_cascade(self, client, db_session):
        user = _create_user(db_session)
        job = _create_job(db_session, user.id, "Acme")
        headers = _auth(user)

        client.post("/api/cover-letter", headers=headers, json={
            "title": "CL", "content": "body",
            "job_application_id": job.id,
        })
        client.delete(f"/api/jobs/{job.id}", headers=headers)

        r = client.get("/api/cover-letter", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 1
