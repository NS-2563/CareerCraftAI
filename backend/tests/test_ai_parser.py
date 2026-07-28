"""Unit tests for Phase 2D — AI-Assisted Resume Parsing.

Tests cover:
- Successful AI parsing (valid JSON)
- Markdown-wrapped JSON
- Malformed JSON repair
- Schema validation failure
- Gemini failure / timeout
- Deterministic fallback
- Merge precedence
- Missing sections
- Long input / chunking
- Sensitive data not appearing in logs
- End-to-end pipeline
"""
import json
import logging
from unittest.mock import patch, ANY

import pytest

from app.resume.services.ai_parser import (
    _parse_ai_json_response,
    _validate_section_data,
    _merge_section,
    parse_section_with_ai,
    enrich_deterministic_with_ai,
    AIParseResult,
)
from app.resume.services.resume_pipeline import parse_resume_full
from app.resume.services.resume_prompt import get_section_prompt
from app.schemas.resume import ResumeCreate


# =========================================================================
# Test data
# =========================================================================

VALID_PERSONAL_JSON = {
    "firstName": "John",
    "lastName": "Doe",
    "title": "Software Engineer",
    "email": "john@example.com",
    "phone": "(555) 123-4567",
    "location": "San Francisco, CA",
    "linkedin": "https://linkedin.com/in/johndoe",
    "github": "https://github.com/johndoe",
    "portfolio": "https://johndoe.dev",
}

VALID_EXPERIENCE_JSON = [
    {
        "company": "Acme Corp",
        "position": "Senior Engineer",
        "location": "San Francisco, CA",
        "startDate": "2021",
        "endDate": "2024",
        "current": False,
        "description": "Led a team of 5 engineers. Reduced deployment time by 60%.",
    },
    {
        "company": "Beta Inc",
        "position": "Junior Dev",
        "location": "",
        "startDate": "2018",
        "endDate": "2021",
        "current": False,
        "description": "Built REST APIs. Maintained CI/CD pipelines.",
    },
]

VALID_EDUCATION_JSON = [
    {
        "institution": "Stanford University",
        "degree": "M.S.",
        "fieldOfStudy": "Computer Science",
        "location": "Stanford, CA",
        "startDate": "2016",
        "endDate": "2018",
        "current": False,
        "gpa": "3.9",
        "description": "",
    },
]

MARKDOWN_WRAPPED = (
    "Here is the parsed resume data:\n\n"
    "```json\n"
    '{"firstName": "Jane", "lastName": "Smith"}\n'
    "```\n"
)

MALFORMED_JSON = (
    '{"firstName": "Jane", "lastName": "Smith",}'
)

TRUNCATED_JSON = '{"firstName": "Jane", "lastName": "Smith", "email": "jane@email.com"'

SAMPLE_RESUME_TEXT = (
    "Jane Smith\n"
    "jane.smith@email.com\n"
    "(555) 123-4567\n"
    "San Francisco, CA\n"
    "linkedin.com/in/janesmith\n"
    "github.com/janesmith\n\n"
    "Professional Summary\n"
    "Results-driven software engineer with 6 years of experience "
    "building scalable web applications.\n\n"
    "Work Experience\n"
    "Acme Corp | Senior Engineer | San Francisco | 2021-Present\n"
    "Led a team of 5 engineers.\n"
    "Reduced deployment time by 60%.\n\n"
    "Education\n"
    "Stanford University | M.S. Computer Science | 2018-2020\n"
    "GPA: 3.9/4.0\n\n"
    "Skills\n"
    "Python, JavaScript, React, AWS\n\n"
    "Languages\n"
    "English (Native), Spanish (Fluent)\n\n"
    "References\n"
    "Available upon request."
)

LONG_SECTION_TEXT = "Skill\n" * 5000  # >8000 chars for chunking test


# =========================================================================
# JSON parsing tests
# =========================================================================

class TestParseAiJsonResponse:
    def test_valid_json(self):
        result = _parse_ai_json_response(json.dumps(VALID_PERSONAL_JSON))
        assert result == VALID_PERSONAL_JSON

    def test_markdown_wrapped(self):
        result = _parse_ai_json_response(MARKDOWN_WRAPPED)
        assert result == {"firstName": "Jane", "lastName": "Smith"}

    def test_malformed_json_repair(self):
        result = _parse_ai_json_response(MALFORMED_JSON)
        assert result == {"firstName": "Jane", "lastName": "Smith"}

    def test_truncated_json_returns_none(self):
        result = _parse_ai_json_response(TRUNCATED_JSON)
        assert result is None

    def test_empty_string(self):
        assert _parse_ai_json_response("") is None

    def test_none_input(self):
        assert _parse_ai_json_response(None) is None

    def test_non_json_text(self):
        assert _parse_ai_json_response("This is not JSON at all") is None


# =========================================================================
# Schema validation tests
# =========================================================================

class TestValidateSectionData:
    def test_valid_personal(self):
        result = _validate_section_data("personal", VALID_PERSONAL_JSON)
        assert result is not None
        assert result["firstName"] == "John"
        assert result["email"] == "john@example.com"

    def test_invalid_personal(self):
        result = _validate_section_data("personal", "not a dict")
        assert result is None

    def test_valid_experience(self):
        result = _validate_section_data("experience", VALID_EXPERIENCE_JSON)
        assert result is not None
        assert len(result) == 2
        assert result[0]["company"] == "Acme Corp"

    def test_invalid_experience_item(self):
        result = _validate_section_data("experience", [{"invalid_key": "value"}])
        # Should still return the entry with empty fields
        assert result is not None
        assert len(result) == 1

    def test_empty_list_section(self):
        result = _validate_section_data("skills", [])
        assert result == []

    def test_none_data(self):
        assert _validate_section_data("personal", None) is None

    def test_dict_wrapped_list(self):
        # Single dict should be wrapped into list for list sections
        result = _validate_section_data("experience", VALID_EXPERIENCE_JSON[0])
        assert result is not None
        assert len(result) == 1

    def test_summary_validation(self):
        result = _validate_section_data("summary", {"summary": "Test summary"})
        assert result == {"summary": "Test summary"}

    def test_summary_empty(self):
        result = _validate_section_data("summary", {})
        assert result is None


# =========================================================================
# Merge logic tests
# =========================================================================

class TestMergeSection:
    def test_personal_deterministic_wins_high_confidence(self):
        det = {"firstName": "John", "lastName": "Doe", "email": "", "title": ""}
        ai = {"firstName": "Wrong", "lastName": "Name", "email": "john@email.com", "title": "Engineer"}
        merged, source = _merge_section("personal", det, ai)
        assert merged["firstName"] == "John"  # deterministic wins
        assert merged["lastName"] == "Doe"
        assert merged["email"] == "john@email.com"  # AI fills empty
        assert merged["title"] == "Engineer"  # AI fills empty
        assert source["firstName"] == "rule"
        assert source["email"] == "ai"

    def test_personal_ai_fills_empty(self):
        det = {"firstName": "John", "lastName": "Doe"}
        ai = {"firstName": "John", "lastName": "Doe", "location": "SF, CA"}
        merged, _ = _merge_section("personal", det, ai)
        assert merged["location"] == "SF, CA"

    def test_personal_no_ai(self):
        det = {"firstName": "John", "lastName": "Doe"}
        merged, source = _merge_section("personal", det, None)
        assert merged == det
        assert source["firstName"] == "rule"

    def test_experience_deterministic_fields_win(self):
        det = [
            {"company": "Acme Corp", "position": "Engineer", "description": "Short desc.", "startDate": "2020", "endDate": "2022", "current": False, "location": ""}
        ]
        ai = [
            {"company": "Acme Corp", "position": "Engineer", "description": "Full AI description with lots of details.", "startDate": "2020", "endDate": "2022", "current": False, "location": "NYC"}
        ]
        merged, source = _merge_section("experience", det, ai)
        assert merged[0]["company"] == "Acme Corp"  # deterministic wins
        assert merged[0]["position"] == "Engineer"
        assert merged[0]["startDate"] == "2020"
        assert merged[0]["endDate"] == "2022"
        assert merged[0]["current"] is False
        # Description length < threshold → AI fills
        assert "Full AI description" in merged[0]["description"]
        # Location empty in det → AI fills
        assert merged[0]["location"] == "NYC"

    def test_experience_no_ai_match_uses_det(self):
        det = [{"company": "Acme Corp", "position": "Engineer"}]
        merged, _ = _merge_section("experience", det, None)
        assert len(merged) == 1
        assert merged[0]["company"] == "Acme Corp"

    def test_experience_no_det_uses_ai(self):
        ai = [{"company": "Acme Corp", "position": "Engineer", "description": "Great work."}]
        merged, _ = _merge_section("experience", None, ai)
        assert len(merged) == 1
        assert merged[0]["company"] == "Acme Corp"

    def test_skills_dedup_merge(self):
        det = [{"name": "Python"}, {"name": "Java"}]
        ai = [{"name": "Python"}, {"name": "React"}]
        merged, _ = _merge_section("skills", det, ai)
        # Should have Python, Java, React
        names = [s["name"] for s in merged]
        assert "Python" in names
        assert "Java" in names
        assert "React" in names

    def test_summary_ai_preferred_when_longer(self):
        det = "Short summary"
        ai = {"summary": "Longer and more detailed summary text here."}
        merged, source = _merge_section("summary", det, ai)
        assert merged == "Longer and more detailed summary text here."
        assert source["summary"] == "ai"

    def test_summary_det_preferred_when_ai_shorter(self):
        det = "Longer deterministic summary that is very detailed."
        ai = {"summary": "Short"}
        merged, _ = _merge_section("summary", det, ai)
        assert merged == "Longer deterministic summary that is very detailed."

    def test_empty_det_and_ai(self):
        merged, _ = _merge_section("skills", [], [])
        assert merged == []


# =========================================================================
# AI parsing (with mocked provider)
# =========================================================================

class TestParseSectionWithAi:
    @patch("app.resume.services.ai_parser._call_ai")
    def test_successful_parse_personal(self, mock_call_ai):
        mock_call_ai.return_value = json.dumps(VALID_PERSONAL_JSON)
        result = parse_section_with_ai("personal", "John Doe\njohn@email.com")
        assert result.success is True
        assert result.error is None
        assert result.data["firstName"] == "John"

    @patch("app.resume.services.ai_parser._call_ai")
    def test_markdown_wrapped_response(self, mock_call_ai):
        mock_call_ai.return_value = MARKDOWN_WRAPPED
        result = parse_section_with_ai("personal", "Jane Smith")
        assert result.success is True
        assert result.data["firstName"] == "Jane"

    @patch("app.resume.services.ai_parser._call_ai")
    def test_malformed_json_response(self, mock_call_ai):
        mock_call_ai.return_value = MALFORMED_JSON
        result = parse_section_with_ai("personal", "Jane Smith")
        assert result.success is True
        assert result.data["firstName"] == "Jane"

    @patch("app.resume.services.ai_parser._call_ai")
    def test_ai_call_failure_fallback(self, mock_call_ai):
        mock_call_ai.return_value = None
        det_context = {"firstName": "Jane", "lastName": "Smith"}
        result = parse_section_with_ai("personal", "Jane Smith", det_context)
        assert result.success is False
        assert result.data == det_context  # falls back to deterministic
        assert "AI call failed" in result.error

    @patch("app.resume.services.ai_parser._call_ai")
    def test_ai_throws_exception_fallback(self, mock_call_ai):
        mock_call_ai.side_effect = Exception("API unavailable")
        result = parse_section_with_ai("personal", "Jane Smith")
        assert result.success is False

    @patch("app.resume.services.ai_parser._call_ai")
    def test_schema_validation_failure_fallback(self, mock_call_ai):
        mock_call_ai.return_value = '{"invalid": "data", "bad": 123}'
        det_context = {"firstName": "Fallback", "lastName": "User"}
        result = parse_section_with_ai("personal", "text", det_context)
        assert result.success is False
        assert result.data["firstName"] == "Fallback"

    @patch("app.resume.services.ai_parser._call_ai")
    def test_empty_section_text(self, mock_call_ai):
        result = parse_section_with_ai("personal", "", {"firstName": "Existing"})
        assert result.success is True
        assert result.data["firstName"] == "Existing"

    @patch("app.resume.services.ai_parser._call_ai")
    def test_unsupported_section(self, mock_call_ai):
        result = parse_section_with_ai("unknown_section", "text")
        assert result.success is False
        assert "unsupported" in result.error.lower()

    @patch("app.resume.services.ai_parser._call_ai")
    def test_truncated_json_fallback(self, mock_call_ai):
        mock_call_ai.return_value = TRUNCATED_JSON
        det_context = {"firstName": "Fallback", "lastName": "User"}
        result = parse_section_with_ai("personal", "text", det_context)
        assert result.success is False
        assert result.data["firstName"] == "Fallback"


# =========================================================================
# Full enrichment tests
# =========================================================================

class TestEnrichDeterministicWithAi:
    @patch("app.resume.services.ai_parser._call_ai")
    def test_all_sections_succeed(self, mock_call_ai):
        mock_call_ai.return_value = json.dumps(VALID_PERSONAL_JSON)
        det = {
            "personal": {"firstName": "John", "lastName": "Doe"},
            "summary": "Test",
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "languages": [],
            "interests": [],
            "references": [],
            "achievements": "",
        }
        sections = {k: "" for k in det}
        sections["header"] = "John Doe"

        merged, meta = enrich_deterministic_with_ai(det, sections)
        assert merged["personal"]["firstName"] == "John"
        assert "ai_success" in meta["personal"]

    @patch("app.resume.services.ai_parser._call_ai")
    def test_partial_ai_failure(self, mock_call_ai):
        """Personal section AI works, experience fails."""
        def side_effect(prompt):
            if "personal" in prompt:
                return json.dumps(VALID_PERSONAL_JSON)
            return None

        mock_call_ai.side_effect = side_effect
        det = {
            "personal": {"firstName": "John", "lastName": "Doe"},
            "summary": "",
            "experience": [{"company": "Acme Corp", "position": "Engineer"}],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "languages": [],
            "interests": [],
            "references": [],
            "achievements": "",
        }
        sections = {k: "" for k in det}
        sections["header"] = "John Doe"
        sections["experience"] = "Acme Corp | Engineer"

        merged, meta = enrich_deterministic_with_ai(det, sections)
        assert merged["personal"]["firstName"] == "John"
        assert meta["personal"]["ai_success"] is True
        assert meta["experience"]["ai_success"] is False
        assert merged["experience"][0]["company"] == "Acme Corp"

    @patch("app.resume.services.ai_parser._call_ai")
    def test_all_ai_failure_full_deterministic_fallback(self, mock_call_ai):
        mock_call_ai.return_value = None
        det = {
            "personal": {"firstName": "John"},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "languages": [],
            "interests": [],
            "references": [],
            "achievements": "",
        }
        sections = {k: "" for k in det}
        sections["header"] = "John"
        merged, meta = enrich_deterministic_with_ai(det, sections)
        assert merged["personal"]["firstName"] == "John"
        for section_name in meta:
            assert meta[section_name]["ai_success"] is False


# =========================================================================
# Pipeline tests
# =========================================================================

class TestParseResumeFull:
    def test_deterministic_only_pipeline(self):
        result = parse_resume_full(SAMPLE_RESUME_TEXT, use_ai=False)
        assert result["ai_used"] is False
        assert result["resume_create"] is not None
        assert isinstance(result["resume_create"], ResumeCreate)

    @patch("app.resume.services.ai_parser._call_ai")
    def test_ai_pipeline_all_succeed(self, mock_call_ai):
        mock_call_ai.return_value = json.dumps(VALID_PERSONAL_JSON)
        result = parse_resume_full(SAMPLE_RESUME_TEXT, use_ai=True)
        assert result["ai_used"] is True
        assert isinstance(result["resume_create"], ResumeCreate)

    @patch("app.resume.services.ai_parser._call_ai")
    def test_ai_pipeline_all_fail_deterministic_fallback(self, mock_call_ai):
        mock_call_ai.return_value = None
        result = parse_resume_full(SAMPLE_RESUME_TEXT, use_ai=True)
        assert result["ai_used"] is True
        assert isinstance(result["resume_create"], ResumeCreate)
        # All sections should have ai_success=False
        for section_name, meta in result["source_meta"].items():
            assert meta["ai_success"] is False

    def test_empty_text(self):
        result = parse_resume_full("", "Empty Resume", use_ai=False)
        assert result["resume_create"] is not None
        assert isinstance(result["resume_create"], ResumeCreate)

    def test_pipeline_output_structure(self):
        result = parse_resume_full(SAMPLE_RESUME_TEXT, "Test Resume", use_ai=False)
        assert "resume_create" in result
        assert "source_meta" in result
        assert "enriched_data" in result
        assert "raw_text" in result
        assert "ai_used" in result
        assert "sections" in result
        assert "deterministic" in result


# =========================================================================
# Long input / chunking tests
# =========================================================================

class TestLongInput:
    @patch("app.resume.services.ai_parser._call_ai")
    def test_long_section_skips_ai(self, mock_call_ai):
        """Sections exceeding max chars should skip AI and use deterministic."""
        mock_call_ai.return_value = json.dumps({"name": "Python"})
        det_context = [{"name": "Python"}, {"name": "Java"}]
        result = parse_section_with_ai("skills", LONG_SECTION_TEXT, det_context)
        # Should fall back to deterministic due to length
        assert result.data == det_context
        assert result.source.get("_skipped") == "too_long"


# =========================================================================
# Sensitive data not in logs
# =========================================================================

class TestSensitiveDataLogging:
    @patch("app.resume.services.ai_parser._call_ai")
    def test_sensitive_data_not_logged(self, mock_call_ai, caplog):
        """Verify raw resume content is not in log output."""
        mock_call_ai.return_value = json.dumps(VALID_PERSONAL_JSON)
        caplog.set_level(logging.INFO)

        result = parse_section_with_ai(
            "personal",
            "SSN: 123-45-6789\nSecret info here",
        )

        log_text = caplog.text
        # These should NOT appear in logs
        assert "123-45-6789" not in log_text
        assert "Secret info" not in log_text

    @patch("app.resume.services.ai_parser._call_ai")
    def test_pii_not_in_structured_logs(self, mock_call_ai, caplog):
        """Verify PII is not logged in structured context."""
        mock_call_ai.return_value = None
        caplog.set_level(logging.INFO)

        det = {"firstName": "Jane", "lastName": "Doe", "email": "jane@secret.com"}
        parse_section_with_ai("personal", "", det)

        log_text = caplog.text
        assert "jane@secret.com" not in log_text
        assert "janedoe" not in log_text.lower()

    @patch("app.resume.services.ai_parser._call_ai")
    def test_logging_contains_metadata_not_content(self, mock_call_ai, caplog):
        """Verify logs contain structural metadata, not raw content."""
        mock_call_ai.return_value = None
        caplog.set_level(logging.INFO)

        sections = {k: "" for k in [
            "personal", "summary", "experience", "education", "skills",
            "projects", "certifications", "languages", "interests", "references",
        ]}
        sections["header"] = "Secret PII content"
        det = {
            "personal": {"firstName": "John"},
            "summary": "",
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "languages": [],
            "interests": [],
            "references": [],
            "achievements": "",
        }

        enrich_deterministic_with_ai(det, sections)

        log_text = caplog.text
        assert "Secret PII content" not in log_text


# =========================================================================
# Prompt tests
# =========================================================================

class TestResumePrompt:
    def test_get_section_prompt_exists(self):
        for section in ["personal", "summary", "experience", "education",
                        "skills", "projects", "certifications", "languages",
                        "interests", "references"]:
            prompt = get_section_prompt(section, "test text")
            assert prompt is not None
            assert len(prompt) > 50
            assert "test text" in prompt

    def test_get_section_prompt_with_context(self):
        prompt = get_section_prompt(
            "personal", "John Doe", {"firstName": "John", "lastName": "Doe"}
        )
        assert "firstName" in prompt
        assert "John" in prompt

    def test_unknown_section(self):
        prompt = get_section_prompt("nonexistent", "text")
        assert prompt == ""
