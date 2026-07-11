def rewrite_resume(skills, missing_skills):

    summary = f"""
MCA graduate with strong knowledge in {", ".join(skills[:5])}.
Skilled in software development, problem solving and database management.
Currently enhancing expertise in {", ".join(missing_skills)} to align with industry requirements.
"""

    return {
        "improved_summary": summary.strip()
    }