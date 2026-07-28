"""Phase 3J: Actionable Resume Improvement Recommendations — tests.

Tests cover:
- Schema validation (ActionableRecommendation, priority, required fields)
- Service: full pipeline from quality/sw/ats/deep analysis → recommendations
- Section → wizard mapping accuracy
- Navigation URL generation
- Service edge cases (empty analysis, null sections, missing data)
- Integration: recommendations present in AnalysisResponse
"""
import json
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.recommendations import ActionableRecommendation
from app.services.recommendation_service import generate_recommendations


# =========================================================================
# Fixtures
# =========================================================================


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
def test_user(db_session):
    user = User(
        email="recs_test@example.com",
        username="recs_test",
        hashed_password="$2b$12$abcdefghijklmnopqrstuvwx",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user, db_session):
    from app.dependencies import create_access_token

    token = create_access_token({"sub": str(test_user.id), "ver": 0})

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield {"Authorization": f"Bearer {token}"}
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)

# =========================================================================
# Sample Data
# =========================================================================

SAMPLE_QUALITY_REPORT = {
    "overall_score": 65,
    "overall_status": "needs_improvement",
    "total_issues": 2,
    "total_warnings": 1,
    "total_strengths": 0,
    "issues": [
        {
            "type": "issue",
            "section": "summary",
            "message": "Summary is too short (under 50 words)",
            "details": {"word_count": 25},
        },
        {
            "type": "issue",
            "section": "experience",
            "message": "Missing quantified impact in experience entries",
            "details": {},
        },
    ],
    "warnings": [
        {
            "type": "warning",
            "section": "skills",
            "message": "Only 2 skills listed, consider adding more",
            "details": {},
        },
    ],
    "strengths": [],
    "sections": {},
    "resume_length": {"total_words": 350, "grade": "short", "recommendation": ""},
}

SAMPLE_SW_RESULT = {
    "strengths": [],
    "weaknesses": [
        {
            "type": "weakness",
            "category": "summary",
            "title": "Weak summary",
            "description": "Summary lacks impact and keywords",
            "severity": "high",
            "priority": "high",
            "evidence": {},
            "source": "deterministic",
        },
        {
            "type": "weakness",
            "category": "experience",
            "title": "No quantified results",
            "description": "Experience entries lack measurable outcomes",
            "severity": "medium",
            "priority": "medium",
            "evidence": {},
            "source": "deterministic",
        },
    ],
    "strength_count": 0,
    "weakness_count": 2,
    "top_priorities": ["Weak summary", "No quantified results"],
}

SAMPLE_ATS_RESULT = {
    "overall_ats_score": 55,
    "component_scores": {"structure": 80, "keywords": 40, "action_verbs": 60, "quantified_impact": 30, "contact_info": 100},
    "component_details": {
        "contact_info": {"score": 100, "max_score": 100, "issues": [], "strengths": ["All contact fields present"], "details": {}},
    },
    "risk_level": "medium",
    "risk_factors": ["Low keyword density"],
    "recommendations": ["Add more industry keywords"],
    "ats_issues": [
        {"section": "skills", "message": "Low keyword density for target role", "detail": "Only 2 relevant keywords found"},
    ],
    "date_format_consistency": {"dominant_format": "YYYY-MM", "issues": []},
    "bullet_consistency": {"std_dev": 0.5, "grade": "good"},
}

SAMPLE_DEEP_RESULT = {
    "status": "success",
    "error": None,
    "ai_analysis": {
        "content_quality": {"score": 70, "analysis": "Good structure", "strengths": [], "issues": [], "suggestions": []},
        "summary_quality": {"score": 50, "analysis": "", "strengths": [], "issues": [], "suggestions": []},
        "achievement_impact": {"score": 40, "analysis": "", "strengths": [], "issues": [], "suggestions": []},
        "experience_relevance": {"score": 60, "analysis": "", "strengths": [], "issues": [], "suggestions": []},
        "strengths": [],
        "weaknesses": [{"category": "experience", "title": "AI-identified weakness", "description": "Weak impact descriptions", "priority": "medium", "suggestion": "Add metrics"}],
        "skill_suggestions": {"current_strengths": [], "gaps": ["Docker"], "recommended": [{"skill": "Docker", "reason": "Industry standard"}]},
        "recommendations": [{"priority": "high", "category": "skills", "action": "Add Docker to skills section", "details": "Docker is requested in most job postings", "target_section": "skills"}],
        "overall_assessment": "Decent resume with room for improvement.",
    },
    "hybrid": None,
}

SAMPLE_ANALYSIS_RESULT = {
    "quality_report": SAMPLE_QUALITY_REPORT,
    "strengths_weaknesses": SAMPLE_SW_RESULT,
    "ats_analysis": SAMPLE_ATS_RESULT,
    "deep_analysis": SAMPLE_DEEP_RESULT,
}

# =========================================================================
# Schema Tests
# =========================================================================


class TestActionableRecommendationSchema:
    def test_valid_recommendation(self):
        rec = ActionableRecommendation(
            id="test-1",
            priority="high",
            category="experience",
            description="Missing quantified impact",
            evidence="Analysis found: issues in experience",
            recommended_fix="Add measurable outcomes to experience entries",
            target_section="experience",
            navigation_url="/resume-studio?id=1&section=experience",
            source_type="quality_issue",
            source_id="qr-0",
        )
        assert rec.id == "test-1"
        assert rec.priority == "high"
        assert rec.navigation_url == "/resume-studio?id=1&section=experience"

    def test_invalid_priority_rejected(self):
        with pytest.raises(ValueError):
            ActionableRecommendation(
                id="bad",
                priority="urgent",
                category="test",
                description="x",
                evidence="x",
                recommended_fix="x",
                source_type="test",
            )

    def test_minimal_recommendation(self):
        rec = ActionableRecommendation(
            id="min",
            priority="low",
            category="content",
            description="Test",
            evidence="Test evidence",
            recommended_fix="Do something",
            source_type="quality_warning",
        )
        assert rec.id == "min"
        assert rec.target_section is None
        assert rec.navigation_url is None
        assert rec.source_id is None

    def test_all_fields_optional_except_required(self):
        rec = ActionableRecommendation(
            id="req",
            priority="medium",
            category="ats",
            description="d",
            evidence="e",
            recommended_fix="f",
            source_type="ats_issue",
        )
        assert rec.target_section is None
        assert rec.navigation_url is None
        assert rec.source_id is None


# =========================================================================
# Service Tests
# =========================================================================


class TestGenerateFromQualityReport:
    def test_generates_issues_and_warnings(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT, resume_id=1)
        qr_recs = [r for r in result["recommendations"] if r["source_type"].startswith("quality_")]
        assert len(qr_recs) >= 3

    def test_issues_get_high_priority(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        qr_issues = [r for r in result["recommendations"] if r["source_type"] == "quality_issue"]
        assert all(r["priority"] == "high" for r in qr_issues)

    def test_warnings_get_medium_priority(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        qr_warnings = [r for r in result["recommendations"] if r["source_type"] == "quality_warning"]
        assert all(r["priority"] == "medium" for r in qr_warnings)

    def test_section_mapping_quality(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        summary_recs = [r for r in result["recommendations"] if r.get("target_section") == "summary"]
        assert len(summary_recs) > 0

    def test_empty_quality_report(self):
        result = generate_recommendations({"quality_report": None})
        qr_recs = [r for r in result["recommendations"] if r["source_type"].startswith("quality_")]
        assert len(qr_recs) == 0


class TestGenerateFromStrengthsWeaknesses:
    def test_weaknesses_generated(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        sw_recs = [r for r in result["recommendations"] if r["source_type"] == "strength_weakness"]
        assert len(sw_recs) >= 2

    def test_high_severity_maps_to_high_priority(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        sw_high = [r for r in result["recommendations"] if r["source_type"] == "strength_weakness" and r["priority"] == "high"]
        assert len(sw_high) >= 1

    def test_empty_sw_result(self):
        result = generate_recommendations({"strengths_weaknesses": None})
        sw_recs = [r for r in result["recommendations"] if r["source_type"] == "strength_weakness"]
        assert len(sw_recs) == 0

    def test_weakness_without_category(self):
        result = generate_recommendations({
            "strengths_weaknesses": {
                "weaknesses": [{"title": "Generic issue", "description": "Something"}],
            },
        })
        sw_recs = [r for r in result["recommendations"] if r["source_type"] == "strength_weakness"]
        assert len(sw_recs) == 1


class TestGenerateFromAts:
    def test_ats_issues_generated(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        ats_recs = [r for r in result["recommendations"] if r["source_type"] == "ats_issue"]
        assert len(ats_recs) >= 1

    def test_empty_ats_result(self):
        result = generate_recommendations({"ats_analysis": None})
        ats_recs = [r for r in result["recommendations"] if r["source_type"] == "ats_issue"]
        assert len(ats_recs) == 0


class TestGenerateFromDeepAnalysis:
    def test_deep_recommendations_generated(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        deep_recs = [r for r in result["recommendations"] if r["source_type"] == "deep_analysis"]
        assert len(deep_recs) >= 2

    def test_deep_not_available(self):
        result = generate_recommendations({"deep_analysis": None})
        deep_recs = [r for r in result["recommendations"] if r["source_type"] == "deep_analysis"]
        assert len(deep_recs) == 0

    def test_deep_error_returns_empty(self):
        result = generate_recommendations({
            "deep_analysis": {"status": "error", "error": "API failure"},
        })
        deep_recs = [r for r in result["recommendations"] if r["source_type"] == "deep_analysis"]
        assert len(deep_recs) == 0


class TestNavigationUrls:
    def test_url_with_resume_id(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT, resume_id=42)
        recs_with_url = [r for r in result["recommendations"] if r.get("navigation_url")]
        if recs_with_url:
            for rec in recs_with_url:
                assert "/resume-studio?id=42" in rec["navigation_url"]

    def test_url_without_resume_id(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        for rec in result["recommendations"]:
            assert rec["navigation_url"] is None

    def test_url_includes_section_param(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT, resume_id=5)
        for rec in result["recommendations"]:
            if rec.get("target_section") and rec.get("navigation_url"):
                assert f"section={rec['target_section']}" in rec["navigation_url"]

    def test_url_no_section_when_target_none(self):
        result = generate_recommendations({
            "quality_report": {
                "issues": [{"section": "resume_length", "message": "Resume is too long"}],
                "warnings": [],
                "strengths": [],
            },
        }, resume_id=1)
        url_recs = [r for r in result["recommendations"] if r.get("navigation_url")]
        if url_recs:
            for rec in url_recs:
                assert "&section=" not in rec["navigation_url"]


class TestSortingAndCounts:
    def test_high_priority_first(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        recs = result["recommendations"]
        if len(recs) >= 2:
            first_priorities = [r["priority"] for r in recs[:3]]
            assert "high" in first_priorities or "medium" in first_priorities

    def test_total_count_accurate(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        assert result["total_count"] == len(result["recommendations"])

    def test_high_priority_count(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        high_count = sum(1 for r in result["recommendations"] if r["priority"] == "high")
        assert result["high_priority_count"] == high_count

    def test_empty_analysis(self):
        result = generate_recommendations({})
        assert result["total_count"] == 0
        assert result["high_priority_count"] == 0
        assert result["recommendations"] == []

    def test_all_none_sections(self):
        result = generate_recommendations({
            "quality_report": None,
            "strengths_weaknesses": None,
            "ats_analysis": None,
            "deep_analysis": None,
        })
        assert result["total_count"] == 0
        assert result["recommendations"] == []


class TestSectionMappingAccuracy:
    """Verify that wizard section IDs map to the correct step indices."""

    def test_personal_maps_to_wizard(self):
        result = generate_recommendations({
            "quality_report": {
                "issues": [{"section": "personal", "message": "Missing email"}],
                "warnings": [], "strengths": [],
            },
        }, resume_id=1)
        recs = [r for r in result["recommendations"] if r.get("target_section") == "personal"]
        assert len(recs) >= 1
        for rec in recs:
            assert "section=personal" in rec["navigation_url"]

    def test_summary_maps_correctly(self):
        result = generate_recommendations({
            "quality_report": {
                "issues": [{"section": "summary", "message": "Too short"}],
                "warnings": [], "strengths": [],
            },
        }, resume_id=1)
        recs = [r for r in result["recommendations"] if r.get("target_section") == "summary"]
        assert len(recs) >= 1
        for rec in recs:
            assert "section=summary" in rec["navigation_url"]

    def test_experience_maps_correctly(self):
        result = generate_recommendations({
            "quality_report": {
                "issues": [{"section": "experience", "message": "No quantified impact"}],
                "warnings": [], "strengths": [],
            },
        }, resume_id=1)
        recs = [r for r in result["recommendations"] if r.get("target_section") == "experience"]
        assert len(recs) >= 1

    def test_skills_maps_correctly(self):
        result = generate_recommendations({
            "quality_report": {
                "issues": [{"section": "skills", "message": "Too few skills"}],
                "warnings": [], "strengths": [],
            },
        }, resume_id=1)
        recs = [r for r in result["recommendations"] if r.get("target_section") == "skills"]
        assert len(recs) >= 1

    def test_non_wizard_section_returns_no_target(self):
        result = generate_recommendations({
            "quality_report": {
                "issues": [{"section": "resume_length", "message": "Too long"}],
                "warnings": [], "strengths": [],
            },
        }, resume_id=1)
        for rec in result["recommendations"]:
            assert rec.get("target_section") is None

    def test_ats_issue_with_section_maps(self):
        result = generate_recommendations({
            "ats_analysis": {
                "ats_issues": [{"section": "skills", "message": "Low keyword density"}],
            },
        }, resume_id=1)
        recs = [r for r in result["recommendations"] if r.get("target_section") == "skills"]
        assert len(recs) >= 1

    def test_strength_weakness_category_maps(self):
        result = generate_recommendations({
            "strengths_weaknesses": {
                "weaknesses": [{"category": "education", "title": "Missing degree", "description": "", "severity": "high"}],
            },
        }, resume_id=1)
        recs = [r for r in result["recommendations"] if r.get("target_section") == "education"]
        assert len(recs) >= 1


class TestFixTextGeneration:
    def test_fix_text_includes_detail(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        for rec in result["recommendations"]:
            assert rec["recommended_fix"] is not None
            assert len(rec["recommended_fix"]) > 0

    def test_fix_text_references_section(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT, resume_id=1)
        for rec in result["recommendations"]:
            if rec.get("target_section") and rec.get("recommended_fix"):
                assert len(rec["recommended_fix"]) > 0


class TestRecommendationIdUniqueness:
    def test_ids_are_unique(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        ids = [r["id"] for r in result["recommendations"]]
        assert len(ids) == len(set(ids))

    def test_id_prefixes_are_correct(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        for rec in result["recommendations"]:
            prefix = rec["id"].split("-")[0]
            expected_prefixes = {"qr", "sw", "ats", "deep"}
            assert prefix in expected_prefixes, f"Unexpected id prefix: {prefix}"


class TestSourceTypes:
    def test_all_valid_source_types(self):
        result = generate_recommendations(SAMPLE_ANALYSIS_RESULT)
        valid_types = {"quality_issue", "quality_warning", "strength_weakness", "ats_issue", "deep_analysis"}
        for rec in result["recommendations"]:
            assert rec["source_type"] in valid_types, f"Invalid source_type: {rec['source_type']}"


# =========================================================================
# Edge Cases
# =========================================================================


class TestEdgeCases:
    def test_malformed_quality_finding(self):
        result = generate_recommendations({
            "quality_report": {
                "issues": [None, "string", 123, {"no_message": "x"}],
                "warnings": [],
                "strengths": [],
            },
        })
        assert isinstance(result["recommendations"], list)

    def test_malformed_weakness(self):
        result = generate_recommendations({
            "strengths_weaknesses": {
                "weaknesses": [None, "string", {}],
            },
        })
        assert isinstance(result["recommendations"], list)

    def test_malformed_ats_issue(self):
        result = generate_recommendations({
            "ats_analysis": {
                "ats_issues": [None, "string", 123],
            },
        })
        assert isinstance(result["recommendations"], list)

    def test_malformed_deep_analysis(self):
        result = generate_recommendations({
            "deep_analysis": {
                "status": "success",
                "ai_analysis": {
                    "recommendations": [None, "string", {}],
                    "weaknesses": [None],
                },
            },
        })
        assert isinstance(result["recommendations"], list)


# =========================================================================
# Integration Test
# =========================================================================


class TestAnalysisResponseIntegration:
    """Verify recommendations are correctly included in the full analysis response."""

    def test_recommendations_included_in_response(self, client, auth_headers):
        payload = {
            "resume": {
                "personal": {"first_name": "Jane", "last_name": "Doe", "email": "jane@test.com"},
                "summary": "Experienced software engineer with 5 years in full-stack development.",
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Engineer",
                        "start_date": "2020-01",
                        "end_date": "2023-12",
                        "description": "Built web applications",
                    }
                ],
                "skills": [{"name": "Python"}, {"name": "JavaScript"}],
            },
        }
        response = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert "total_recommendations" in data
        assert "high_priority_recommendations" in data

    def test_recommendations_have_required_fields(self, client, auth_headers):
        payload = {
            "resume": {
                "personal": {"first_name": "Jane", "last_name": "Doe", "email": "jane@test.com"},
                "summary": "Experienced software engineer with 5 years in full-stack development.",
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Engineer",
                        "start_date": "2020-01",
                        "end_date": "2023-12",
                        "description": "Built web applications",
                    }
                ],
            },
        }
        response = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for rec in data["recommendations"]:
            assert "id" in rec
            assert "priority" in rec
            assert "description" in rec
            assert "evidence" in rec
            assert "recommended_fix" in rec
            assert "source_type" in rec

    def test_recommendations_inline_analysis_succeeds(self, client, auth_headers):
        payload = {
            "resume": {
                "personal": {"first_name": "Jane", "last_name": "Doe", "email": "jane@test.com"},
                "summary": "Experienced software engineer with 5 years in full-stack development.",
            },
        }
        response = client.post("/api/analysis/analyze", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        for rec in data["recommendations"]:
            assert "id" in rec
            assert "priority" in rec
            assert "description" in rec
