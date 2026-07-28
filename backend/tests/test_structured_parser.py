"""Unit tests for structured_parser.py — Phase 2C Structured Resume Mapping."""

import pytest

from app.resume.services.parser_utils import (
    normalize_date,
    parse_date_range,
    normalize_url,
    split_entries,
    deduplicate,
)
from app.resume.services.structured_parser import parse_resume
from app.resume.services.parsers.personal import parse_personal
from app.resume.services.parsers.summary import parse_summary
from app.resume.services.parsers.experience import parse_experience
from app.resume.services.parsers.education import parse_education
from app.resume.services.parsers.skills import parse_skills
from app.resume.services.parsers.projects import parse_projects
from app.resume.services.parsers.certifications import parse_certifications
from app.resume.services.parsers.languages import parse_languages
from app.resume.services.parsers.interests import parse_interests
from app.resume.services.parsers.references import parse_references


# =========================================================================
# Utility tests
# =========================================================================

class TestNormalizeDate:
    def test_iso_format(self):
        assert normalize_date("2020-01") == "2020-01"

    def test_mm_yyyy(self):
        assert normalize_date("01/2020") == "2020-01"
        assert normalize_date("1/2020") == "2020-01"

    def test_year_only(self):
        assert normalize_date("2020") == "2020"

    def test_month_name_yyyy(self):
        assert normalize_date("Jan 2020") == "2020-01"
        assert normalize_date("January 2020") == "2020-01"
        assert normalize_date("Dec 2024") == "2024-12"

    def test_yyyy_month_name(self):
        assert normalize_date("2020 Jan") == "2020-01"

    def test_present_returns_empty(self):
        assert normalize_date("Present") == ""
        assert normalize_date("Current") == ""
        assert normalize_date("Now") == ""

    def test_empty(self):
        assert normalize_date("") == ""
        assert normalize_date(None) == ""

    def test_unparseable(self):
        assert normalize_date("someday") == "someday"


class TestParseDateRange:
    def test_yyyy_to_yyyy(self):
        start, end, current = parse_date_range("2020 - 2024")
        assert start == "2020"
        assert end == "2024"
        assert current is False

    def test_month_to_present(self):
        start, end, current = parse_date_range("Jan 2020 - Present")
        assert start == "2020-01"
        assert end == ""
        assert current is True

    def test_mm_yyyy_to_current(self):
        start, end, current = parse_date_range("01/2020 - Current")
        assert start == "2020-01"
        assert end == ""
        assert current is True

    def test_single_date(self):
        start, end, current = parse_date_range("2020")
        assert start == "2020"
        assert end == ""
        assert current is False

    def test_empty(self):
        assert parse_date_range("") == ("", "", False)
        assert parse_date_range(None) == ("", "", False)

    def test_with_hyphen_variants(self):
        start, end, current = parse_date_range("2020–2024")
        assert start == "2020"
        assert end == "2024"


class TestNormalizeUrl:
    def test_already_https(self):
        assert normalize_url("https://example.com") == "https://example.com"

    def test_missing_scheme(self):
        assert normalize_url("example.com") == "https://example.com"

    def test_empty(self):
        assert normalize_url("") == ""
        assert normalize_url(None) == ""

    def test_with_path(self):
        assert normalize_url("github.com/user") == "https://github.com/user"


class TestSplitEntries:
    def test_basic(self):
        result = split_entries("A\n\nB\n\nC")
        assert result == ["A", "B", "C"]

    def test_empty(self):
        assert split_entries("") == []
        assert split_entries(None) == []

    def test_single_entry(self):
        assert split_entries("Just one entry") == ["Just one entry"]

    def test_multi_line_entries(self):
        result = split_entries("Line 1\nLine 2\n\nEntry 2\nLine B")
        assert len(result) == 2
        assert "Line 1\nLine 2" in result


class TestDeduplicate:
    def test_by_name(self):
        items = [{"name": "Python"}, {"name": "python"}, {"name": "Java"}]
        result = deduplicate(items, "name")
        assert len(result) == 2
        assert result[0]["name"] == "Python"

    def test_empty(self):
        assert deduplicate([], "name") == []


# =========================================================================
# Personal info parser tests
# =========================================================================

class TestParsePersonal:
    def test_basic_info(self):
        text = (
            "John Smith\n"
            "john.smith@email.com\n"
            "(555) 123-4567\n"
            "San Francisco, CA\n"
            "linkedin.com/in/johnsmith"
        )
        result = parse_personal(text)
        assert result["firstName"] == "John"
        assert result["lastName"] == "Smith"
        assert result["email"] == "john.smith@email.com"
        assert result["phone"] == "(555) 123-4567"
        assert result["location"] == "San Francisco, CA"
        assert "linkedin.com/in/johnsmith" in result["linkedin"]

    def test_with_title(self):
        text = (
            "Jane Doe\n"
            "Senior Software Engineer\n"
            "jane@email.com"
        )
        result = parse_personal(text)
        assert result["firstName"] == "Jane"
        assert result["lastName"] == "Doe"
        assert result["title"] == "Senior Software Engineer"
        assert result["email"] == "jane@email.com"

    def test_github_and_portfolio(self):
        text = (
            "Alice Wang\n"
            "alice@email.com\n"
            "github.com/alicew\n"
            "alice.dev"
        )
        result = parse_personal(text)
        assert result["firstName"] == "Alice"
        assert result["github"] == "https://github.com/alicew"
        assert result["portfolio"] == "https://alice.dev"

    def test_empty(self):
        result = parse_personal("")
        assert all(v == "" for v in result.values())

    def test_name_with_middle_initial(self):
        text = "Robert J. Williams\nrob@email.com"
        result = parse_personal(text)
        assert result["firstName"] == "Robert"
        assert result["lastName"] == "J. Williams"

    def test_no_email(self):
        text = "Sam Brown\n555-0100"
        result = parse_personal(text)
        assert result["firstName"] == "Sam"
        assert result["email"] == ""


# =========================================================================
# Summary parser tests
# =========================================================================

class TestParseSummary:
    def test_basic(self):
        assert parse_summary("Experienced engineer.") == "Experienced engineer."

    def test_multiline(self):
        text = "Experienced engineer with\n5 years in software development."
        result = parse_summary(text)
        assert "5 years" in result
        assert "\n" not in result

    def test_empty(self):
        assert parse_summary("") == ""
        assert parse_summary(None) == ""


# =========================================================================
# Experience parser tests
# =========================================================================

class TestParseExperience:
    def test_single_entry_pipe_format(self):
        text = (
            "Acme Corp | Software Engineer | San Francisco, CA | 2020-2024\n"
            "Developed RESTful APIs using Python.\n"
            "Led team of 5 engineers."
        )
        result = parse_experience(text)
        assert len(result) == 1
        entry = result[0]
        assert entry["company"] == "Acme Corp"
        assert entry["position"] == "Software Engineer"
        assert entry["location"] == "San Francisco, CA"
        assert entry["startDate"] == "2020"
        assert entry["endDate"] == "2024"
        assert entry["current"] is False
        assert "Developed RESTful APIs" in entry["description"]
        assert "Led team" in entry["description"]

    def test_multiple_entries(self):
        text = (
            "Acme Corp | Engineer | 2020-2024\n"
            "Built APIs.\n\n"
            "Beta Inc | Senior Engineer | 2018-2020\n"
            "Led projects."
        )
        result = parse_experience(text)
        assert len(result) == 2
        assert result[0]["company"] == "Acme Corp"
        assert result[1]["company"] == "Beta Inc"

    def test_present_position(self):
        text = "Acme Corp | Engineer | 2022-Present\nCurrent role."
        result = parse_experience(text)
        assert len(result) == 1
        assert result[0]["startDate"] == "2022"
        assert result[0]["endDate"] == ""
        assert result[0]["current"] is True

    def test_at_format(self):
        text = "Software Engineer at Acme Corp (Jan 2020 - Dec 2024)\nDescription here."
        result = parse_experience(text)
        assert len(result) == 1
        assert result[0]["position"] == "Software Engineer"
        assert result[0]["company"] == "Acme Corp"
        assert result[0]["startDate"] == "2020-01"
        assert result[0]["endDate"] == "2024-12"

    def test_empty(self):
        assert parse_experience("") == []

    def test_multiline_description(self):
        text = (
            "Company | Position | 2020-2024\n"
            "- Led team of 5\n"
            "- Built microservices\n"
            "- Reduced costs by 30%"
        )
        result = parse_experience(text)
        assert len(result) == 1
        assert "Led team of 5" in result[0]["description"]
        assert "Built microservices" in result[0]["description"]

    def test_date_with_month(self):
        text = (
            "Acme Corp | Engineer | Jan 2020 - Mar 2024\n"
            "Did work."
        )
        result = parse_experience(text)
        assert result[0]["startDate"] == "2020-01"
        assert result[0]["endDate"] == "2024-03"


# =========================================================================
# Education parser tests
# =========================================================================

class TestParseEducation:
    def test_pipe_format(self):
        text = "Stanford University | M.S. Computer Science | 2018-2020\nFocus on ML."
        result = parse_education(text)
        assert len(result) == 1
        assert result[0]["institution"] == "Stanford University"
        assert result[0]["degree"] == "M.S. Computer Science"
        assert result[0]["startDate"] == "2018"
        assert result[0]["endDate"] == "2020"
        assert result[0]["current"] is False

    def test_paren_format(self):
        text = "B.S. Computer Science, UC Berkeley (2014-2018)\nGPA: 3.8/4.0"
        result = parse_education(text)
        assert len(result) == 1
        assert result[0]["degree"] == "B.S. Computer Science"
        assert result[0]["institution"] == "UC Berkeley"
        assert result[0]["startDate"] == "2014"
        assert result[0]["endDate"] == "2018"

    def test_gpa_extraction(self):
        text = "Stanford | M.S. | 2018-2020\nGPA: 3.9/4.0"
        result = parse_education(text)
        assert result[0]["gpa"] == "3.9"

    def test_at_format(self):
        text = "M.S. at Stanford University (2018-2020)"
        result = parse_education(text)
        assert result[0]["degree"] == "M.S."
        assert result[0]["institution"] == "Stanford University"

    def test_empty(self):
        assert parse_education("") == []

    def test_location_field(self):
        """Verify location is parsed (was previously missing from schema)."""
        text = "MIT | B.S. | Cambridge, MA | 2014-2018"
        result = parse_education(text)
        assert len(result) == 1
        assert result[0]["location"] == "Cambridge, MA"


# =========================================================================
# Skills parser tests
# =========================================================================

class TestParseSkills:
    def test_comma_separated(self):
        text = "Python, Java, JavaScript, React"
        result = parse_skills(text)
        assert len(result) >= 4
        names = [s["name"] for s in result]
        assert "Python" in names
        assert "Java" in names

    def test_newline_separated(self):
        text = "Python\nJava\nReact"
        result = parse_skills(text)
        assert len(result) == 3

    def test_categorized(self):
        text = "Frontend: React, Vue, TypeScript\nBackend: Python, Node.js"
        result = parse_skills(text)
        assert len(result) >= 5
        frontend = [s for s in result if s["category"] == "Frontend"]
        backend = [s for s in result if s["category"] == "Backend"]
        assert len(frontend) >= 1
        assert len(backend) >= 1

    def test_deduplication(self):
        text = "Python, python, Python, Java"
        result = parse_skills(text)
        names = [s["name"].lower() for s in result]
        assert names.count("python") == 1

    def test_empty(self):
        assert parse_skills("") == []

    def test_mixed_format(self):
        text = (
            "Technical Skills\n"
            "Python, Java\n"
            "Databases: PostgreSQL, MongoDB"
        )
        result = parse_skills(text)
        assert len(result) >= 3


# =========================================================================
# Projects parser tests
# =========================================================================

class TestParseProjects:
    def test_basic(self):
        text = (
            "Resume Builder\n"
            "Built with React, Node.js\n"
            "github.com/user/resume-builder\n"
            "A web app for creating resumes."
        )
        result = parse_projects(text)
        assert len(result) == 1
        assert result[0]["title"] == "Resume Builder"
        assert result[0]["github"] == "https://github.com/user/resume-builder"
        assert "web app" in result[0]["description"]

    def test_with_live_demo(self):
        text = (
            "E-Commerce Platform\n"
            "github.com/user/ecommerce\n"
            "https://myecommerce.com\n"
            "Full-featured online store."
        )
        result = parse_projects(text)
        assert result[0]["liveDemo"] == "https://myecommerce.com"

    def test_empty(self):
        assert parse_projects("") == []


# =========================================================================
# Certifications parser tests
# =========================================================================

class TestParseCertifications:
    def test_basic(self):
        text = (
            "AWS Certified Solutions Architect — Amazon Web Services\n"
            "Issued: Jan 2022\n"
            "https://aws.amazon.com/certification"
        )
        result = parse_certifications(text)
        assert len(result) == 1
        assert result[0]["name"] == "AWS Certified Solutions Architect"
        assert result[0]["issuer"] == "Amazon Web Services"
        assert result[0]["issueDate"] == "2022-01"
        assert "aws.amazon.com" in result[0]["credentialUrl"]

    def test_pipe_format(self):
        text = "PMP | Project Management Institute | 2023"
        result = parse_certifications(text)
        assert result[0]["name"] == "PMP"
        assert result[0]["issuer"] == "Project Management Institute"
        assert result[0]["issueDate"] == "2023"

    def test_empty(self):
        assert parse_certifications("") == []


# =========================================================================
# Languages parser tests
# =========================================================================

class TestParseLanguages:
    def test_basic(self):
        text = "English (Native), Spanish (Fluent)"
        result = parse_languages(text)
        assert len(result) >= 2
        langs = {r["language"].lower(): r["proficiency"] for r in result}
        assert "english" in langs
        assert "spanish" in langs

    def test_pipe_separated(self):
        text = "English | Native\nSpanish | Fluent"
        result = parse_languages(text)
        assert len(result) >= 2

    def test_empty(self):
        assert parse_languages("") == []

    def test_deduplication(self):
        text = "English (Native), English (Fluent)"
        result = parse_languages(text)
        assert len(result) == 1


# =========================================================================
# Interests parser tests
# =========================================================================

class TestParseInterests:
    def test_comma_separated(self):
        text = "Hiking, Photography, Open Source"
        result = parse_interests(text)
        assert len(result) == 3
        assert result[0]["name"] == "Hiking"

    def test_newline_separated(self):
        text = "Chess\nRunning\nReading"
        result = parse_interests(text)
        assert len(result) == 3

    def test_empty(self):
        assert parse_interests("") == []

    def test_deduplication(self):
        text = "Music, Music, Art"
        result = parse_interests(text)
        assert len(result) == 2


# =========================================================================
# References parser tests
# =========================================================================

class TestParseReferences:
    def test_basic(self):
        text = (
            "John Smith\n"
            "Senior Manager at Acme Corp\n"
            "john.smith@email.com\n"
            "(555) 123-4567"
        )
        result = parse_references(text)
        assert len(result) == 1
        assert result[0]["name"] == "John Smith"
        assert result[0]["designation"] == "Senior Manager"
        assert result[0]["organization"] == "Acme Corp"
        assert result[0]["email"] == "john.smith@email.com"
        assert result[0]["phone"] == "(555) 123-4567"

    def test_available_upon_request(self):
        assert parse_references("Available upon request.") == []
        assert parse_references("References available on request.") == []

    def test_empty(self):
        assert parse_references("") == []

    def test_multiple_references(self):
        text = (
            "John Smith\n"
            "Manager at Acme Corp\n"
            "john@email.com\n\n"
            "Jane Doe\n"
            "Director at Beta Inc\n"
            "jane@email.com"
        )
        result = parse_references(text)
        assert len(result) == 2
        assert result[0]["name"] == "John Smith"
        assert result[1]["name"] == "Jane Doe"


# =========================================================================
# Orchestrator (parse_resume) integration tests
# =========================================================================

class TestParseResume:
    def test_full_resume(self):
        text = (
            "Jane Smith\n"
            "jane.smith@email.com\n"
            "(555) 123-4567\n"
            "San Francisco, CA\n"
            "linkedin.com/in/janesmith\n"
            "github.com/janesmith\n\n"
            "Professional Summary\n"
            "Results-driven software engineer with 6 years of experience\n"
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
            "Certifications\n"
            "AWS Certified Solutions Architect — Amazon Web Services | 2022\n\n"
            "Languages\n"
            "English (Native), Spanish (Fluent)\n\n"
            "Interests\n"
            "Open Source, Hiking\n\n"
            "References\n"
            "Available upon request."
        )
        result = parse_resume(text)

        # Personal
        assert result["personal"]["firstName"] == "Jane"
        assert result["personal"]["lastName"] == "Smith"
        assert result["personal"]["email"] == "jane.smith@email.com"

        # Summary
        assert "software engineer" in result["summary"]

        # Experience
        assert len(result["experience"]) == 1
        assert result["experience"][0]["company"] == "Acme Corp"
        assert result["experience"][0]["current"] is True

        # Education
        assert len(result["education"]) == 1
        assert result["education"][0]["institution"] == "Stanford University"
        assert result["education"][0]["gpa"] == "3.9"

        # Skills
        assert len(result["skills"]) >= 3

        # Certifications
        assert len(result["certifications"]) == 1
        assert "AWS Certified" in result["certifications"][0]["name"]

        # Languages
        assert len(result["languages"]) >= 2

        # Interests
        assert len(result["interests"]) == 2

        # References — "available upon request" returns empty
        assert result["references"] == []

        # Achievements preserved as raw text
        assert result["achievements"] == ""

    def test_minimal_resume(self):
        text = (
            "Bob Wilson\n"
            "bob@email.com\n\n"
            "Experience\n"
            "Acme Corp | Engineer | 2020-2024\n"
            "Did stuff."
        )
        result = parse_resume(text)
        assert result["personal"]["firstName"] == "Bob"
        assert len(result["experience"]) == 1
        assert result["summary"] == ""
        assert result["education"] == []
        assert result["skills"] == []
        assert result["projects"] == []
        assert result["certifications"] == []
        assert result["languages"] == []
        assert result["interests"] == []
        assert result["references"] == []

    def test_no_headings(self):
        text = "Just some random text without section headings."
        result = parse_resume(text)
        assert result["personal"] == {
            "firstName": "", "lastName": "", "title": "",
            "email": "", "phone": "", "location": "",
            "linkedin": "", "github": "", "portfolio": "",
        }
        assert result["summary"] == ""
        assert result["experience"] == []
        assert result["education"] == []

    def test_empty_text(self):
        result = parse_resume("")
        assert result["personal"]["firstName"] == ""
        assert result["summary"] == ""
        assert result["experience"] == []

    def test_achievements_preserved(self):
        text = (
            "Summary\nSummary text.\n\n"
            "Achievements\nAwarded Best Engineer 2023.\n"
            "Increased revenue by 40%."
        )
        result = parse_resume(text)
        assert "Awarded Best Engineer 2023" in result["achievements"]
        assert "Increased revenue by 40%" in result["achievements"]


# =========================================================================
# Edge case and malformed data tests
# =========================================================================

class TestEdgeCases:
    def test_unusual_date_formats(self):
        text = "Company | Position | 01/2020 - 12/2024\nWork."
        result = parse_experience(text)
        assert result[0]["startDate"] == "2020-01"
        assert result[0]["endDate"] == "2024-12"

    def test_bullet_list_description(self):
        text = (
            "Company | Position | 2020-2024\n"
            "• Built feature X\n"
            "• Fixed bug Y\n"
            "• Optimized performance Z"
        )
        result = parse_experience(text)
        assert "Built feature X" in result[0]["description"]

    def test_missing_date(self):
        text = "Acme Corp | Engineer\nWorked on stuff."
        result = parse_experience(text)
        assert result[0]["company"] == "Acme Corp"
        assert result[0]["startDate"] == ""

    def test_partial_personal_info(self):
        text = "john@email.com"
        result = parse_personal(text)
        assert result["email"] == "john@email.com"
        assert result["firstName"] == ""

    def test_skills_with_levels(self):
        text = "Python (Advanced), SQL (Intermediate)"
        result = parse_skills(text)
        names = [s["name"] for s in result]
        assert "Python" in names
        assert "SQL" in names

    def test_multiple_education_entries(self):
        text = (
            "MIT | B.S. Computer Science | 2014-2018\n"
            "Stanford | M.S. Computer Science | 2018-2020\n"
            "GPA: 4.0"
        )
        result = parse_education(text)
        assert len(result) == 2

    def test_projects_with_tech_stack(self):
        text = (
            "Resume Builder\n"
            "Technologies: React, Node.js, PostgreSQL\n"
            "Built a full-stack resume creation tool."
        )
        result = parse_projects(text)
        assert "React" in result[0]["techStack"]
        assert "full-stack" in result[0]["description"]

    def test_references_without_organization(self):
        text = (
            "John Smith\n"
            "john@email.com\n"
            "555-0100"
        )
        result = parse_references(text)
        assert result[0]["name"] == "John Smith"
        assert result[0]["email"] == "john@email.com"
