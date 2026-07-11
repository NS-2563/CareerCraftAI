from app.ai.gemini_service import ask_gemini

def optimize_resume(resume, job_role):

    prompt = f"""
You are an expert resume reviewer.

Target Job Role:
{job_role}

Resume:
{resume}

Rewrite the resume professionally.

Improve:

1. Professional Summary
2. Skills
3. Project Descriptions
4. Experience
5. ATS Keywords

Return the optimized resume in a clean format.
"""

    return ask_gemini(prompt)