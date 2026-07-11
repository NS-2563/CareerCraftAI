"""Prompts package for AI services."""
from app.prompts.summary import generate_summary_prompt, improve_summary_prompt
from app.prompts.experience import improve_experience_prompt
from app.prompts.project import improve_project_prompt
from app.prompts.skills import suggest_skills_prompt
from app.prompts.analysis import analyze_resume_prompt

__all__ = [
    "generate_summary_prompt",
    "improve_summary_prompt",
    "improve_experience_prompt",
    "improve_project_prompt",
    "suggest_skills_prompt",
    "analyze_resume_prompt",
]