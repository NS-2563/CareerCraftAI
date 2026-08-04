"""Tests for Dashboard "Today's Focus" — signal-backed top recommendation."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.dashboard.service import DashboardService
from app.dashboard.focus_service import (
    CATEGORY_NEW_SKILL,
    CATEGORY_RESUME_WORDING,
    CATEGORY_PRACTICE,
    categorize_recommendation,
    get_today_focus,
    get_today_focus_items,
)


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


@pytest.fixture
def client(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestSession = sessionmaker(bind=connection)
    session = TestSession()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, email="focus@test.com", username="focustester",
                 password="Test1234!"):
    from app.dependencies import get_password_hash
    from app.models.user import User
    u = User(email=email, username=username,
             hashed_password=get_password_hash(password), is_active=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _create_career_report(db, user_id, priority, readiness_score=70):
    from app.models.career_report import CareerReport
    cr = CareerReport(
        user_id=user_id,
        career_goal="Software Engineer",
        readiness_score=readiness_score,
        source="ai",
        report_json={"skill_gap": {"priority": priority}},
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    return cr


def _login(client, email="focus@test.com", password="Test1234!"):
    resp = client.post("/api/auth/login", json={
        "email": email,
        "password": password,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Unit: categorize_recommendation
# ---------------------------------------------------------------------------

class TestCategorizeRecommendation:

    def test_jd_missing_skill_maps_to_new_skill(self):
        rec = {
            "skill": "Kubernetes",
            "reasons": [
                "Missing in 3 of 5 saved job matches",
                "Reinforced in your learning roadmap",
            ],
        }
        assert categorize_recommendation(rec)["category"] == CATEGORY_NEW_SKILL

    def test_resume_analysis_maps_to_resume_wording(self):
        rec = {
            "skill": "TypeScript",
            "reasons": [
                "Flagged as a skill to add in your resume analysis",
                "Reinforced in your learning roadmap",
            ],
        }
        assert categorize_recommendation(rec)["category"] == CATEGORY_RESUME_WORDING

    def test_interview_weakness_maps_to_practice(self):
        rec = {
            "skill": "System Design",
            "reasons": ["Targets your weakest interview area (System Design)"],
        }
        assert categorize_recommendation(rec)["category"] == CATEGORY_PRACTICE

    def test_unrecognized_reasons_default_to_new_skill(self):
        rec = {"skill": "Docker", "reasons": ["Random unexplained reason"]}
        assert categorize_recommendation(rec)["category"] == CATEGORY_NEW_SKILL

    def test_mixed_reasons_pick_dominant_category(self):
        rec = {
            "skill": "GraphQL",
            "reasons": [
                "Missing in 2 of 4 saved job matches",
                "Flagged as a skill to add in your resume analysis",
                "Targets your weakest interview area (APIs)",
            ],
        }
        assert categorize_recommendation(rec)["category"] == CATEGORY_NEW_SKILL

    def test_resume_wording_beats_practice_when_equally_counted(self):
        rec = {
            "skill": "SQL",
            "reasons": [
                "Flagged as a skill to add in your resume analysis",
                "Targets your weakest interview area (SQL)",
            ],
        }
        assert categorize_recommendation(rec)["category"] == CATEGORY_RESUME_WORDING

    def test_missing_reasons_key_is_safe(self):
        rec = {"skill": "Go"}
        result = categorize_recommendation(rec)
        assert result["category"] == CATEGORY_NEW_SKILL
        assert result["reasons"] == []


# ---------------------------------------------------------------------------
# Unit: get_today_focus selection
# ---------------------------------------------------------------------------

class TestTodayFocusSelection:

    def test_no_report_returns_none(self, db_session):
        user = _create_user(db_session)
        assert get_today_focus(db_session, user.id) is None

    def test_no_priority_entries_returns_none(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[])
        assert get_today_focus(db_session, user.id) is None

    def test_zero_supported_signals_returns_none(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "Kubernetes",
                "supported_signals": 0,
                "total_possible_signals": 4,
                "reasons": ["Missing in 3 of 5 saved job matches"],
            },
        ])
        assert get_today_focus(db_session, user.id) is None

    def test_picks_highest_ratio(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "Kubernetes",
                "supported_signals": 1,
                "total_possible_signals": 4,
                "reasons": ["Missing in 3 of 5 saved job matches"],
            },
            {
                "skill": "TypeScript",
                "supported_signals": 3,
                "total_possible_signals": 4,
                "reasons": ["Flagged as a skill to add in your resume analysis"],
            },
        ])
        focus = get_today_focus(db_session, user.id)
        assert focus["skill"] == "TypeScript"
        assert focus["category"] == CATEGORY_RESUME_WORDING
        assert focus["supported_signals"] == 3
        assert focus["total_possible_signals"] == 4
        assert focus["reasons"] == [
            "Flagged as a skill to add in your resume analysis"
        ]

    def test_equal_ratio_prefers_single_signal_category(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "Kubernetes",
                "supported_signals": 2,
                "total_possible_signals": 4,
                "reasons": [
                    "Missing in 3 of 5 saved job matches",
                    "Reinforced in your learning roadmap",
                ],
            },
            {
                "skill": "Docker",
                "supported_signals": 2,
                "total_possible_signals": 4,
                "reasons": ["Targets your weakest interview area (Containers)"],
            },
        ])
        focus = get_today_focus(db_session, user.id)
        assert focus["skill"] == "Docker"
        assert focus["category"] == CATEGORY_PRACTICE

    def test_equal_ratio_and_ease_prefers_more_signals(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "SQL",
                "supported_signals": 1,
                "total_possible_signals": 4,
                "reasons": ["Targets your weakest interview area (SQL)"],
            },
            {
                "skill": "Go",
                "supported_signals": 2,
                "total_possible_signals": 4,
                "reasons": ["Targets your weakest interview area (Backend)"],
            },
        ])
        focus = get_today_focus(db_session, user.id)
        assert focus["skill"] == "Go"

    def test_fully_equal_break_by_alpha(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "Zig",
                "supported_signals": 2,
                "total_possible_signals": 4,
                "reasons": ["Targets your weakest interview area (Zig)"],
            },
            {
                "skill": "Rust",
                "supported_signals": 2,
                "total_possible_signals": 4,
                "reasons": ["Targets your weakest interview area (Rust)"],
            },
        ])
        focus = get_today_focus(db_session, user.id)
        assert focus["skill"] == "Rust"

    def test_skips_malformed_entries(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            None,
            {"skill": 42, "supported_signals": 3, "total_possible_signals": 4},
            {"skill": "", "supported_signals": 3, "total_possible_signals": 4},
            {
                "skill": "Python",
                "supported_signals": 3,
                "total_possible_signals": 4,
                "reasons": ["Missing in 2 of 5 saved job matches"],
            },
        ])
        focus = get_today_focus(db_session, user.id)
        assert focus["skill"] == "Python"

    def test_uses_latest_report(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "OldSkill",
                "supported_signals": 4,
                "total_possible_signals": 4,
                "reasons": ["Missing in 5 of 5 saved job matches"],
            },
        ])
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "NewSkill",
                "supported_signals": 1,
                "total_possible_signals": 4,
                "reasons": ["Missing in 1 of 5 saved job matches"],
            },
        ])
        focus = get_today_focus(db_session, user.id)
        assert focus["skill"] == "NewSkill"

    def test_legacy_string_report_json_is_safe(self, db_session):
        from app.models.career_report import CareerReport
        user = _create_user(db_session)
        cr = CareerReport(
            user_id=user.id, career_goal="SWE", readiness_score=70,
            source="ai", report_json="not-a-dict",
        )
        db_session.add(cr)
        db_session.commit()
        assert get_today_focus(db_session, user.id) is None

    def test_scoped_per_user(self, db_session):
        user_a = _create_user(db_session, email="a@test.com", username="usera")
        user_b = _create_user(db_session, email="b@test.com", username="userb")
        _create_career_report(db_session, user_a.id, priority=[
            {
                "skill": "AOnly",
                "supported_signals": 3,
                "total_possible_signals": 4,
                "reasons": ["Missing in 2 of 5 saved job matches"],
            },
        ])
        assert get_today_focus(db_session, user_a.id)["skill"] == "AOnly"
        assert get_today_focus(db_session, user_b.id) is None


# ---------------------------------------------------------------------------
# Unit: get_today_focus_items top-N
# ---------------------------------------------------------------------------

class TestTodayFocusItems:

    def test_returns_top_three_ordered_by_ratio(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "Low",
                "supported_signals": 1, "total_possible_signals": 4,
                "reasons": ["Missing in 1 of 5 saved job matches"],
            },
            {
                "skill": "High",
                "supported_signals": 4, "total_possible_signals": 4,
                "reasons": ["Missing in 5 of 5 saved job matches"],
            },
            {
                "skill": "Mid",
                "supported_signals": 2, "total_possible_signals": 4,
                "reasons": ["Flagged as a skill to add in your resume analysis"],
            },
            {
                "skill": "Dropped",
                "supported_signals": 0, "total_possible_signals": 4,
                "reasons": ["Missing in 1 of 5 saved job matches"],
            },
        ])
        items = get_today_focus_items(db_session, user.id, limit=3)
        assert [i["skill"] for i in items] == ["High", "Mid", "Low"]
        # zero-signal "Dropped" never appears
        assert all(i["skill"] != "Dropped" for i in items)

    def test_partial_top_three_when_fewer_candidates(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "Only",
                "supported_signals": 2, "total_possible_signals": 4,
                "reasons": ["Missing in 2 of 5 saved job matches"],
            },
        ])
        items = get_today_focus_items(db_session, user.id, limit=3)
        assert len(items) == 1
        assert items[0]["skill"] == "Only"

    def test_empty_when_no_report(self, db_session):
        user = _create_user(db_session)
        assert get_today_focus_items(db_session, user.id, limit=3) == []

    def test_recommends_its_own_top_when_limit_one(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "A",
                "supported_signals": 1, "total_possible_signals": 4,
                "reasons": ["Missing in 1 of 5 saved job matches"],
            },
            {
                "skill": "B",
                "supported_signals": 3, "total_possible_signals": 4,
                "reasons": ["Flagged as a skill to add in your resume analysis"],
            },
        ])
        assert get_today_focus_items(db_session, user.id, limit=1)[0]["skill"] == "B"


# ---------------------------------------------------------------------------
# Integration: via DashboardService.get_summary and the API
# ---------------------------------------------------------------------------

class TestTodayFocusDashboardIntegration:

    def test_summary_includes_today_focus(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "Terraform",
                "supported_signals": 3,
                "total_possible_signals": 4,
                "reasons": ["Missing in 2 of 5 saved job matches"],
            },
        ])
        summary = DashboardService.get_summary(db_session, user.id)
        assert summary["today_focus"]["skill"] == "Terraform"
        assert summary["today_focus"]["category"] == CATEGORY_NEW_SKILL

    def test_summary_includes_focus_items(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "K8s",
                "supported_signals": 3, "total_possible_signals": 4,
                "reasons": ["Missing in 2 of 5 saved job matches"],
            },
            {
                "skill": "SQL",
                "supported_signals": 2, "total_possible_signals": 4,
                "reasons": ["Flagged as a skill to add in your resume analysis"],
            },
        ])
        summary = DashboardService.get_summary(db_session, user.id)
        assert [i["skill"] for i in summary["focus_items"]] == ["K8s", "SQL"]

    def test_summary_focus_items_empty_for_new_user(self, db_session):
        user = _create_user(db_session)
        summary = DashboardService.get_summary(db_session, user.id)
        assert summary["today_focus"] is None
        assert summary["focus_items"] == []

    def test_api_returns_focus_items(self, db_session, client):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "GCP",
                "supported_signals": 2, "total_possible_signals": 4,
                "reasons": ["Targets your weakest interview area (Cloud)"],
            },
            {
                "skill": "AWS",
                "supported_signals": 1, "total_possible_signals": 4,
                "reasons": ["Missing in 1 of 5 saved job matches"],
            },
        ])
        token = _login(client)
        resp = client.get("/api/dashboard/summary", headers=_auth_headers(token))
        assert resp.status_code == 200, resp.text
        items = resp.json()["data"]["focus_items"]
        assert [i["skill"] for i in items] == ["GCP", "AWS"]

    def test_summary_today_focus_none_for_new_user(self, db_session):
        user = _create_user(db_session)
        summary = DashboardService.get_summary(db_session, user.id)
        assert summary["today_focus"] is None

    def test_summary_today_focus_none_when_all_zero_signals(self, db_session):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "Spark",
                "supported_signals": 0,
                "total_possible_signals": 4,
                "reasons": [],
            },
        ])
        summary = DashboardService.get_summary(db_session, user.id)
        assert summary["today_focus"] is None

    def test_api_returns_today_focus(self, db_session, client):
        user = _create_user(db_session)
        _create_career_report(db_session, user.id, priority=[
            {
                "skill": "GCP",
                "supported_signals": 2,
                "total_possible_signals": 4,
                "reasons": ["Targets your weakest interview area (Cloud)"],
            },
        ])
        token = _login(client)
        resp = client.get(
            "/api/dashboard/summary",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200, resp.text
        focus = resp.json()["data"]["today_focus"]
        assert focus["skill"] == "GCP"
        assert focus["category"] == CATEGORY_PRACTICE
        assert focus["supported_signals"] == 2
        assert focus["total_possible_signals"] == 4

    def test_api_today_focus_none_for_new_user(self, db_session, client):
        _create_user(db_session)
        token = _login(client)
        resp = client.get(
            "/api/dashboard/summary",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["today_focus"] is None
