"""Unit tests for section_detector.py — Phase 2B Resume Section Detection."""

import pytest

from app.resume.services.section_detector import detect_sections


# ---------------------------------------------------------------------------
# Heading variation tests
# ---------------------------------------------------------------------------

class TestSummaryHeadings:
    def test_professional_summary(self):
        text = "John Doe\njohn@email.com\n\nProfessional Summary\nA dedicated engineer with 5 years of experience."
        result = detect_sections(text)
        assert "A dedicated engineer with 5 years of experience." in result["summary"]

    def test_summary_heading(self):
        text = "Summary\nQualified professional with expertise in Python."
        result = detect_sections(text)
        assert "Qualified professional with expertise in Python." in result["summary"]

    def test_profile_heading(self):
        text = "Profile\nResults-driven manager with 10 years of leadership."
        result = detect_sections(text)
        assert "Results-driven manager with 10 years of leadership." in result["summary"]

    def test_objective_heading(self):
        text = "Objective\nTo obtain a challenging position in software engineering."
        result = detect_sections(text)
        assert "To obtain a challenging position" in result["summary"]

    def test_career_objective(self):
        text = "Career Objective\nSeeking a role in data science."
        result = detect_sections(text)
        assert "Seeking a role in data science." in result["summary"]

    def test_personal_statement(self):
        text = "Personal Statement\nA creative problem solver."
        result = detect_sections(text)
        assert "A creative problem solver." in result["summary"]

    def test_about_me(self):
        text = "About Me\nPassionate developer and open source contributor."
        result = detect_sections(text)
        assert "Passionate developer" in result["summary"]

    def test_summary_with_colon(self):
        text = "Summary: A seasoned professional with 8 years of experience."
        result = detect_sections(text)
        assert "A seasoned professional with 8 years of experience." in result["summary"]

    def test_summary_of_qualifications(self):
        text = "Summary of Qualifications\nExtensive experience in project management."
        result = detect_sections(text)
        assert "Extensive experience" in result["summary"]

    def test_summary_of_skills(self):
        text = "Summary of Skills\nPython, Java, SQL, Cloud Computing"
        result = detect_sections(text)
        assert "Python, Java, SQL, Cloud Computing" in result["summary"]


class TestExperienceHeadings:
    def test_experience(self):
        text = "Experience\nSoftware Engineer at Acme Corp (2020-2024)"
        result = detect_sections(text)
        assert "Software Engineer at Acme Corp" in result["experience"]

    def test_work_experience(self):
        text = "Work Experience\nDeveloper at Beta Inc."
        result = detect_sections(text)
        assert "Developer at Beta Inc." in result["experience"]

    def test_professional_experience(self):
        text = "Professional Experience\nSenior Engineer at Gamma LLC."
        result = detect_sections(text)
        assert "Senior Engineer at Gamma LLC." in result["experience"]

    def test_employment_history(self):
        text = "Employment History\nFull Stack Developer (2018-2022)"
        result = detect_sections(text)
        assert "Full Stack Developer (2018-2022)" in result["experience"]

    def test_career_history(self):
        text = "Career History\nLead Developer at Delta Corp."
        result = detect_sections(text)
        assert "Lead Developer at Delta Corp." in result["experience"]

    def test_work_history(self):
        text = "Work History\nJunior Developer at Epsilon Inc."
        result = detect_sections(text)
        assert "Junior Developer at Epsilon Inc." in result["experience"]

    def test_professional_background(self):
        text = "Professional Background\n15 years in software development."
        result = detect_sections(text)
        assert "15 years in software development." in result["experience"]

    def test_relevant_experience(self):
        text = "Relevant Experience\nDesigned and built microservices."
        result = detect_sections(text)
        assert "Designed and built microservices." in result["experience"]

    def test_experience_with_colon_inline(self):
        text = "Experience: Acme Corp, Software Engineer, 2020-2024"
        result = detect_sections(text)
        assert "Acme Corp, Software Engineer, 2020-2024" in result["experience"]


class TestEducationHeadings:
    def test_education(self):
        text = "Education\nB.S. Computer Science, MIT"
        result = detect_sections(text)
        assert "B.S. Computer Science, MIT" in result["education"]

    def test_education_and_qualifications(self):
        text = "Education and Qualifications\nPhD in Machine Learning"
        result = detect_sections(text)
        assert "PhD in Machine Learning" in result["education"]

    def test_academic_background(self):
        text = "Academic Background\nBA in Economics, Harvard"
        result = detect_sections(text)
        assert "BA in Economics, Harvard" in result["education"]

    def test_academic_history(self):
        text = "Academic History\nMaster of Science, Stanford"
        result = detect_sections(text)
        assert "Master of Science, Stanford" in result["education"]

    def test_qualifications(self):
        text = "Qualifications\nMBA, University of Chicago"
        result = detect_sections(text)
        assert "MBA, University of Chicago" in result["education"]

    def test_education_with_colon(self):
        text = "Education: B.S. Computer Science"
        result = detect_sections(text)
        assert "B.S. Computer Science" in result["education"]


class TestSkillsHeadings:
    def test_skills(self):
        text = "Skills\nPython, Java, React, PostgreSQL"
        result = detect_sections(text)
        assert "Python, Java, React, PostgreSQL" in result["skills"]

    def test_technical_skills(self):
        text = "Technical Skills\nDocker, Kubernetes, AWS"
        result = detect_sections(text)
        assert "Docker, Kubernetes, AWS" in result["skills"]

    def test_core_competencies(self):
        text = "Core Competencies\nLeadership, Communication, Problem Solving"
        result = detect_sections(text)
        assert "Leadership, Communication, Problem Solving" in result["skills"]

    def test_areas_of_expertise(self):
        text = "Areas of Expertise\nCloud Architecture, DevOps, Security"
        result = detect_sections(text)
        assert "Cloud Architecture, DevOps, Security" in result["skills"]

    def test_area_of_expertise(self):
        text = "Area of Expertise\nData Engineering"
        result = detect_sections(text)
        assert "Data Engineering" in result["skills"]

    def test_tools_and_technologies(self):
        text = "Tools and Technologies\nGit, Jenkins, Terraform"
        result = detect_sections(text)
        assert "Git, Jenkins, Terraform" in result["skills"]

    def test_technologies(self):
        text = "Technologies\nReact, Node.js, TypeScript"
        result = detect_sections(text)
        assert "React, Node.js, TypeScript" in result["skills"]

    def test_competencies(self):
        text = "Competencies\nStrategic Planning, Team Leadership"
        result = detect_sections(text)
        assert "Strategic Planning, Team Leadership" in result["skills"]

    def test_tools(self):
        text = "Tools\nVS Code, Docker, Postman"
        result = detect_sections(text)
        assert "VS Code, Docker, Postman" in result["skills"]

    def test_skills_colon_inline(self):
        text = "Skills: Python, Java, React"
        result = detect_sections(text)
        assert "Python, Java, React" in result["skills"]

    def test_skills_and_abilities(self):
        text = "Skills and Abilities\nPublic Speaking, Technical Writing"
        result = detect_sections(text)
        assert "Public Speaking, Technical Writing" in result["skills"]

    def test_skills_and_expertise(self):
        text = "Skills and Expertise\nMachine Learning, Data Analysis"
        result = detect_sections(text)
        assert "Machine Learning, Data Analysis" in result["skills"]


class TestProjectsHeadings:
    def test_projects(self):
        text = "Projects\nBuilt a real-time chat application"
        result = detect_sections(text)
        assert "Built a real-time chat application" in result["projects"]

    def test_personal_projects(self):
        text = "Personal Projects\nOpen source contribution to React"
        result = detect_sections(text)
        assert "Open source contribution" in result["projects"]

    def test_side_projects(self):
        text = "Side Projects\nMobile app for task management"
        result = detect_sections(text)
        assert "Mobile app for task management" in result["projects"]

    def test_key_projects(self):
        text = "Key Projects\nLed migration to microservices architecture"
        result = detect_sections(text)
        assert "Led migration to microservices" in result["projects"]

    def test_notable_projects(self):
        text = "Notable Projects\nDesigned fault-tolerant distributed system"
        result = detect_sections(text)
        assert "Designed fault-tolerant" in result["projects"]

    def test_project_experience(self):
        text = "Project Experience\nDeveloped CI/CD pipeline for 50+ services"
        result = detect_sections(text)
        assert "Developed CI/CD pipeline" in result["projects"]


class TestCertificationsHeadings:
    def test_certifications(self):
        text = "Certifications\nAWS Certified Solutions Architect"
        result = detect_sections(text)
        assert "AWS Certified Solutions Architect" in result["certifications"]

    def test_professional_certifications(self):
        text = "Professional Certifications\nPMP, CISSP, CISM"
        result = detect_sections(text)
        assert "PMP, CISSP, CISM" in result["certifications"]

    def test_licenses_and_certifications(self):
        text = "Licenses and Certifications\nCPA License, CFA Charterholder"
        result = detect_sections(text)
        assert "CPA License, CFA Charterholder" in result["certifications"]

    def test_licenses(self):
        text = "Licenses\nReal Estate License - State of California"
        result = detect_sections(text)
        assert "Real Estate License" in result["certifications"]

    def test_license(self):
        text = "License\nMedical License - State of New York"
        result = detect_sections(text)
        assert "Medical License" in result["certifications"]

    def test_certifications_with_colon(self):
        text = "Certifications: AWS Certified, Google Cloud Certified"
        result = detect_sections(text)
        assert "AWS Certified, Google Cloud Certified" in result["certifications"]


class TestLanguagesHeadings:
    def test_languages(self):
        text = "Languages\nEnglish (Native), Spanish (Fluent)"
        result = detect_sections(text)
        assert "English (Native), Spanish (Fluent)" in result["languages"]

    def test_linguistic_abilities(self):
        text = "Linguistic Abilities\nFrench (Advanced), German (Intermediate)"
        result = detect_sections(text)
        assert "French (Advanced), German (Intermediate)" in result["languages"]

    def test_language_proficiency(self):
        text = "Language Proficiency\nMandarin (Native), Japanese (Conversational)"
        result = detect_sections(text)
        assert "Mandarin (Native), Japanese (Conversational)" in result["languages"]


class TestInterestsHeadings:
    def test_interests(self):
        text = "Interests\nOpen Source, Hiking, Photography"
        result = detect_sections(text)
        assert "Open Source, Hiking, Photography" in result["interests"]

    def test_hobbies(self):
        text = "Hobbies\nChess, Running, Reading"
        result = detect_sections(text)
        assert "Chess, Running, Reading" in result["interests"]

    def test_activities(self):
        text = "Activities\nVolunteering, Rock Climbing, Cooking"
        result = detect_sections(text)
        assert "Volunteering, Rock Climbing, Cooking" in result["interests"]

    def test_personal_interests(self):
        text = "Personal Interests\nTravel, Music, Art"
        result = detect_sections(text)
        assert "Travel, Music, Art" in result["interests"]


class TestReferencesHeadings:
    def test_references(self):
        text = "References\nAvailable upon request."
        result = detect_sections(text)
        assert "Available upon request." in result["references"]

    def test_professional_references(self):
        text = "Professional References\nJohn Smith, Manager at Acme Corp"
        result = detect_sections(text)
        assert "John Smith, Manager at Acme Corp" in result["references"]


class TestAchievementsHeadings:
    def test_achievements(self):
        text = "Achievements\nEmployee of the Month (3x), Top Sales Award 2023"
        result = detect_sections(text)
        assert "Employee of the Month" in result["achievements"]

    def test_accomplishments(self):
        text = "Accomplishments\nIncreased revenue by 40% through process optimization."
        result = detect_sections(text)
        assert "Increased revenue by 40%" in result["achievements"]

    def test_awards(self):
        text = "Awards\nBest Innovation Award 2022, Excellence in Engineering"
        result = detect_sections(text)
        assert "Best Innovation Award 2022" in result["achievements"]

    def test_honors(self):
        text = "Honors\nDean's List, Summa Cum Laude"
        result = detect_sections(text)
        assert "Dean's List, Summa Cum Laude" in result["achievements"]

    def test_honors_and_awards(self):
        text = "Honors and Awards\nPresidential Scholarship, Research Grant"
        result = detect_sections(text)
        assert "Presidential Scholarship, Research Grant" in result["achievements"]

    def test_key_achievements(self):
        text = "Key Achievements\nLed team to deliver project 2 months early."
        result = detect_sections(text)
        assert "Led team to deliver project" in result["achievements"]

    def test_notable_achievements(self):
        text = "Notable Achievements\nPublished 5 research papers in top journals."
        result = detect_sections(text)
        assert "Published 5 research papers" in result["achievements"]


class TestPersonalHeader:
    def test_personal_information(self):
        text = "Personal Information\nJohn Doe\njohn@email.com\n555-0100"
        result = detect_sections(text)
        assert "John Doe" in result["header"]
        assert "john@email.com" in result["header"]
        assert "555-0100" in result["header"]

    def test_contact_information(self):
        text = "Contact Information\nJane Smith\njane@email.com"
        result = detect_sections(text)
        assert "Jane Smith" in result["header"]

    def test_contact_details(self):
        text = "Contact Details\nBob Wilson\nbob@email.com"
        result = detect_sections(text)
        assert "Bob Wilson" in result["header"]

    def test_personal_details(self):
        text = "Personal Details\nAlice Brown\nalice@email.com"
        result = detect_sections(text)
        assert "Alice Brown" in result["header"]

    def test_contact_information_with_colon(self):
        text = "Contact Information: Jane Smith, jane@email.com"
        result = detect_sections(text)
        assert "Jane Smith, jane@email.com" in result["header"]

    def test_header_before_first_section(self):
        text = "John Doe\njohn@email.com\n\nProfessional Summary\n5 years of experience."
        result = detect_sections(text)
        assert "John Doe" in result["header"]
        assert "john@email.com" in result["header"]
        assert "5 years of experience." in result["summary"]


# ---------------------------------------------------------------------------
# Multi-section and ordering tests
# ---------------------------------------------------------------------------

class TestMultipleSections:
    def test_standard_order(self):
        text = (
            "John Doe\njohn@email.com\n\n"
            "Summary\nExperienced engineer.\n\n"
            "Experience\nWorked at Acme Corp.\n\n"
            "Education\nMIT\n\n"
            "Skills\nPython, Java"
        )
        result = detect_sections(text)
        assert "Experienced engineer." in result["summary"]
        assert "Worked at Acme Corp." in result["experience"]
        assert "MIT" in result["education"]
        assert "Python, Java" in result["skills"]
        assert "John Doe" in result["header"]

    def test_all_sections(self):
        text = (
            "Contact Information\nJohn\n\n"
            "Summary\nSummary text\n\n"
            "Experience\nExp text\n\n"
            "Education\nEdu text\n\n"
            "Skills\nSkill text\n\n"
            "Projects\nProj text\n\n"
            "Certifications\nCert text\n\n"
            "Languages\nLang text\n\n"
            "Interests\nInt text\n\n"
            "References\nRef text\n\n"
            "Achievements\nAch text"
        )
        result = detect_sections(text)
        assert result["header"] == "John"
        assert result["summary"] == "Summary text"
        assert result["experience"] == "Exp text"
        assert result["education"] == "Edu text"
        assert result["skills"] == "Skill text"
        assert result["projects"] == "Proj text"
        assert result["certifications"] == "Cert text"
        assert result["languages"] == "Lang text"
        assert result["interests"] == "Int text"
        assert result["references"] == "Ref text"
        assert result["achievements"] == "Ach text"

    def test_reordered_sections(self):
        text = (
            "Skills\nPython\n\n"
            "Education\nMIT\n\n"
            "Experience\nEngineer"
        )
        result = detect_sections(text)
        assert result["skills"] == "Python"
        assert result["education"] == "MIT"
        assert result["experience"] == "Engineer"


# ---------------------------------------------------------------------------
# Missing section tests
# ---------------------------------------------------------------------------

class TestMissingSections:
    def test_only_summary(self):
        text = "Summary\nSome text."
        result = detect_sections(text)
        assert result["summary"] == "Some text."
        assert result["experience"] == ""
        assert result["education"] == ""
        assert result["skills"] == ""
        assert result["projects"] == ""
        assert result["certifications"] == ""
        assert result["languages"] == ""
        assert result["interests"] == ""
        assert result["references"] == ""
        assert result["achievements"] == ""

    def test_only_experience(self):
        text = "Work Experience\nWorked at Google."
        result = detect_sections(text)
        assert result["experience"] == "Worked at Google."
        assert result["summary"] == ""

    def test_no_personal_section(self):
        text = "Summary\nJust a summary."
        result = detect_sections(text)
        assert result["header"] == ""
        assert result["summary"] == "Just a summary."

    def test_only_header_no_headings(self):
        text = "John Doe\njohn@email.com\n555-0100"
        result = detect_sections(text)
        # No heading detected -> goes to unknown
        assert result["header"] == ""
        assert result["unknown"] == "John Doe\njohn@email.com\n555-0100"
        assert all(result[s] == "" for s in ["summary", "experience", "education",
                                              "skills", "projects", "certifications",
                                              "languages", "interests", "references",
                                              "achievements"])

    def test_missing_middle_section(self):
        text = (
            "Summary\nSummary text.\n\n"
            "Experience\nWork history.\n\n"
            "Skills\nPython skills."
        )
        result = detect_sections(text)
        assert result["summary"] == "Summary text."
        assert result["experience"] == "Work history."
        assert result["skills"] == "Python skills."
        assert result["education"] == ""
        assert result["projects"] == ""
        assert result["certifications"] == ""
        assert result["languages"] == ""
        assert result["interests"] == ""
        assert result["references"] == ""
        assert result["achievements"] == ""


# ---------------------------------------------------------------------------
# False positive tests
# ---------------------------------------------------------------------------

class TestFalsePositives:
    def test_experience_in_sentence_rejected(self):
        """'Experience' used mid-sentence should NOT trigger a section."""
        text = "I have experience in software development and project management."
        result = detect_sections(text)
        assert result["experience"] == ""

    def test_skills_in_sentence_rejected(self):
        """'Skills' used mid-sentence should NOT trigger a section."""
        text = "I developed strong analytical skills during my tenure."
        result = detect_sections(text)
        assert result["skills"] == ""

    def test_education_in_sentence_rejected(self):
        text = "Education is the foundation of professional growth."
        result = detect_sections(text)
        assert result["education"] == ""

    def test_summary_in_paragraph_rejected(self):
        text = "A summary of my qualifications includes the following achievements."
        result = detect_sections(text)
        assert result["summary"] == ""

    def test_projects_in_paragraph_rejected(self):
        text = "I managed multiple projects simultaneously."
        result = detect_sections(text)
        assert result["projects"] == ""

    def test_experience_with_non_colon_continuation(self):
        """'Experience is...' should NOT trigger a section."""
        text = "Experience is the best teacher."
        result = detect_sections(text)
        assert result["experience"] == ""

    def test_awards_in_sentence_rejected(self):
        text = "The awards ceremony was held in March."
        result = detect_sections(text)
        assert result["achievements"] == ""

    def test_interests_in_sentence_rejected(self):
        text = "My interests include machine learning and data science."
        result = detect_sections(text)
        assert result["interests"] == ""

    def test_references_in_sentence_rejected(self):
        text = "References are available upon request from previous employers."
        result = detect_sections(text)
        assert result["references"] == ""

    def test_heading_word_at_line_start_with_content(self):
        """Line starting with heading word + non-colon content = not a heading."""
        text = "Skills required for this position include Python and Java."
        result = detect_sections(text)
        assert result["skills"] == ""


# ---------------------------------------------------------------------------
# Multi-page text tests
# ---------------------------------------------------------------------------

class TestMultiPageText:
    def test_two_pages(self):
        text = (
            "Page 1 header content...\n\n"
            "Summary\nSummary from page 1.\n\n"
            "Experience\nExperience from page 1.\n\n"
            "--- PAGE BREAK ---\n\n"
            "Education\nEducation from page 2.\n\n"
            "Skills\nSkills from page 2."
        )
        result = detect_sections(text)
        assert "Summary from page 1." in result["summary"]
        assert "Experience from page 1." in result["experience"]
        assert "Education from page 2." in result["education"]
        assert "Skills from page 2." in result["skills"]

    def test_section_spanning_pages(self):
        text = (
            "Experience\nCompany A (page 1 content)\n\n"
            "--- PAGE BREAK ---\n"
            "Company A continued (page 2 content)\n\n"
            "Education\nMIT"
        )
        result = detect_sections(text)
        assert "Company A (page 1 content)" in result["experience"]
        assert "Company A continued (page 2 content)" in result["experience"]
        assert "MIT" in result["education"]


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_string(self):
        result = detect_sections("")
        assert all(v == "" for v in result.values())

    def test_only_whitespace(self):
        result = detect_sections("   \n  \n  ")
        assert all(v == "" for v in result.values())

    def test_single_line(self):
        result = detect_sections("Just a single line of text without headings.")
        assert result["unknown"] == "Just a single line of text without headings."
        assert result["header"] == ""

    def test_newlines_only(self):
        result = detect_sections("\n\n\n")
        assert all(v == "" for v in result.values())

    def test_heading_with_trailing_whitespace(self):
        text = "  Experience  \n  Worked at Google."
        result = detect_sections(text)
        assert result["experience"] == "Worked at Google."

    def test_heading_with_colon_and_whitespace(self):
        text = "  Skills  :  Python, Java  "
        result = detect_sections(text)
        assert result["skills"] == "Python, Java"

    def test_case_insensitivity(self):
        text = "EXPERIENCE\nWorked at Google."
        result = detect_sections(text)
        assert result["experience"] == "Worked at Google."

        text = "Summary\nEngineer."
        result = detect_sections(text)
        assert result["summary"] == "Engineer."

        text = "SKILLS\nPython"
        result = detect_sections(text)
        assert result["skills"] == "Python"

    def test_mixed_case(self):
        text = "Work Experience\nEngineer."
        result = detect_sections(text)
        assert result["experience"] == "Engineer."

        text = "PROFESSIONAL SUMMARY\nEngineer."
        result = detect_sections(text)
        assert result["summary"] == "Engineer."

    def test_content_after_last_section(self):
        text = (
            "Summary\nSummary text.\n\n"
            "Experience\nWork history.\n\n"
            "This text appears after the last heading and should belong to experience."
        )
        result = detect_sections(text)
        assert "Work history." in result["experience"]
        assert "This text appears after the last heading" in result["experience"]

    def test_text_before_first_heading(self):
        text = "John Doe\njohn@email.com\n\nProfessional Summary\nSummary here."
        result = detect_sections(text)
        assert result["header"] == "John Doe\njohn@email.com"
        assert result["summary"] == "Summary here."

    def test_only_unknown_section_no_headings_found(self):
        text = (
            "This is a resume with no clear section headings.\n"
            "Just paragraphs of text describing experience and skills.\n"
            "But nothing that looks like a standalone heading."
        )
        result = detect_sections(text)
        assert result["header"] == ""
        assert result["unknown"] == text.strip()
        assert result["experience"] == ""
        assert result["skills"] == ""

    def test_duplicate_heading_maps_to_same_section(self):
        text = (
            "Skills\nPython\n\n"
            "Skills\nJava"
        )
        result = detect_sections(text)
        assert "Python" in result["skills"]
        assert "Java" in result["skills"]

    def test_blank_lines_between_sections(self):
        text = (
            "Summary\nSummary text.\n\n\n\n"
            "Experience\nWork history."
        )
        result = detect_sections(text)
        assert result["summary"] == "Summary text."
        assert result["experience"] == "Work history."


# ---------------------------------------------------------------------------
# Two-column layout simulation tests
# ---------------------------------------------------------------------------

class TestTwoColumnLayout:
    def test_interleaved_two_column(self):
        """Simulate two-column PDF extraction where lines may interleave."""
        text = (
            "Skills\n"
            "Python\n"
            "Java\n"
            "React\n"
            "Education\n"
            "MIT\n"
            "Stanford"
        )
        result = detect_sections(text)
        assert "Python" in result["skills"]
        assert "Java" in result["skills"]
        assert "React" in result["skills"]
        assert "MIT" in result["education"]
        assert "Stanford" in result["education"]


# ---------------------------------------------------------------------------
# TypeError test
# ---------------------------------------------------------------------------

class TestTypeError:
    def test_non_string_input(self):
        with pytest.raises(TypeError, match="Expected str"):
            detect_sections(None)  # type: ignore

    def test_integer_input(self):
        with pytest.raises(TypeError, match="Expected str"):
            detect_sections(123)  # type: ignore

    def test_dict_input(self):
        with pytest.raises(TypeError, match="Expected str"):
            detect_sections({})  # type: ignore


# ---------------------------------------------------------------------------
# Realistic resume simulation tests
# ---------------------------------------------------------------------------

class TestRealisticResume:
    def test_simple_resume(self):
        text = (
            "Jane Smith\n"
            "jane.smith@email.com\n"
            "(555) 123-4567\n"
            "San Francisco, CA\n\n"
            "Professional Summary\n"
            "Results-driven software engineer with 6 years of experience building\n"
            "scalable web applications using Python and JavaScript.\n\n"
            "Work Experience\n"
            "Senior Software Engineer | Acme Corp | 2021-Present\n"
            "Led a team of 5 engineers to deliver a microservices platform.\n"
            "Reduced deployment time by 60% through CI/CD automation.\n\n"
            "Software Engineer | Beta Inc | 2018-2021\n"
            "Built RESTful APIs serving 1M+ daily requests.\n"
            "Implemented real-time data processing pipeline.\n\n"
            "Education\n"
            "M.S. Computer Science | Stanford University | 2016-2018\n"
            "B.S. Computer Science | UC Berkeley | 2012-2016\n\n"
            "Skills\n"
            "Python, JavaScript, TypeScript, React, Node.js, PostgreSQL,\n"
            "Docker, Kubernetes, AWS, Terraform, CI/CD\n\n"
            "Certifications\n"
            "AWS Certified Solutions Architect\n"
            "Kubernetes Administrator (CKA)\n\n"
            "Languages\n"
            "English (Native), Spanish (Fluent)\n\n"
            "Interests\n"
            "Open Source, Hiking, Photography"
        )
        result = detect_sections(text)

        assert "Jane Smith" in result["header"]
        assert "jane.smith@email.com" in result["header"]
        assert "(555) 123-4567" in result["header"]

        assert "Results-driven software engineer" in result["summary"]
        assert "scalable web applications" in result["summary"]

        assert "Senior Software Engineer | Acme Corp" in result["experience"]
        assert "Software Engineer | Beta Inc" in result["experience"]
        assert "microservices platform" in result["experience"]
        assert "RESTful APIs" in result["experience"]

        assert "M.S. Computer Science | Stanford University" in result["education"]
        assert "B.S. Computer Science | UC Berkeley" in result["education"]

        assert "Python, JavaScript, TypeScript" in result["skills"]
        assert "Docker, Kubernetes, AWS" in result["skills"]

        assert "AWS Certified Solutions Architect" in result["certifications"]
        assert "Kubernetes Administrator (CKA)" in result["certifications"]

        assert "English (Native), Spanish (Fluent)" in result["languages"]

        assert "Open Source, Hiking, Photography" in result["interests"]

        assert result["references"] == ""
        assert result["achievements"] == ""

    def test_resume_with_achievements(self):
        text = (
            "John Doe\n"
            "john@email.com\n\n"
            "Summary\n"
            "Accomplished manager with 10 years of experience.\n\n"
            "Experience\n"
            "Manager at Acme Corp\n"
            "Led team of 20.\n\n"
            "Achievements\n"
            "Increased revenue by 40%.\n"
            "Employee of the Year 2023."
        )
        result = detect_sections(text)
        assert "Accomplished manager" in result["summary"]
        assert "Manager at Acme Corp" in result["experience"]
        assert "Led team of 20." in result["experience"]
        assert "Increased revenue by 40%." in result["achievements"]
        assert "Employee of the Year 2023." in result["achievements"]
