from app.ai.gemini_service import ask_gemini

def generate_cover_letter(name, job_role, company, skills):

    prompt = f"""
Write a professional cover letter.

Candidate Name:
{name}

Job Role:
{job_role}

Company:
{company}

Skills:
{skills}

The letter should include:

- Introduction
- Why the candidate fits the role
- Technical strengths
- Closing paragraph

Keep it professional and ATS-friendly.
"""

    return ask_gemini(prompt)