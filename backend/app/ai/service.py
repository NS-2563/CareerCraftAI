"""AI Service layer using provider architecture."""
import logging
from typing import Any, Dict, List, Optional

from app.providers.factory import get_provider

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI operations using configurable provider."""

    @staticmethod
    def generate_summary(personal: Dict[str, Any]) -> str:
        """Generate a professional summary from personal info.

        Args:
            personal: Dictionary containing personal information

        Returns:
            Generated professional summary

        Raises:
            ValueError: If provider is not configured
            Exception: For other provider errors
        """
        provider = get_provider()
        return provider.generate_summary(personal)

    @staticmethod
    def improve_summary(summary: str) -> str:
        """Improve an existing summary.

        Args:
            summary: The original summary to improve

        Returns:
            Improved summary text
        """
        provider = get_provider()
        return provider.improve_summary(summary)

    @staticmethod
    def improve_experience(
        description: str, position: Optional[str] = None, company: Optional[str] = None
    ) -> str:
        """Improve experience description.

        Args:
            description: The original experience description
            position: Job position title
            company: Company name

        Returns:
            Improved experience description
        """
        provider = get_provider()
        return provider.improve_experience(description, position, company)

    @staticmethod
    def improve_project(description: str, name: Optional[str] = None) -> str:
        """Improve project description.

        Args:
            description: The original project description
            name: Project name

        Returns:
            Improved project description
        """
        provider = get_provider()
        return provider.improve_project(description, name)

    @staticmethod
    def suggest_skills(
        current_skills: List[str],
        job_title: Optional[str] = None,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Suggest relevant skills based on current skills and job target.

        Args:
            current_skills: List of current skills
            job_title: Target job title
            job_description: Target job description

        Returns:
            Dictionary with suggested skills and categories
        """
        provider = get_provider()
        return provider.suggest_skills(current_skills, job_title, job_description)

    @staticmethod
    def analyze_resume(resume: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a resume and provide feedback.

        Args:
            resume: Resume data dictionary

        Returns:
            Dictionary with analysis results
        """
        provider = get_provider()
        return provider.analyze_resume(resume)