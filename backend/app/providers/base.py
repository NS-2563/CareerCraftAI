"""Base AI Provider interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate_summary(self, personal: Dict[str, Any]) -> str:
        """Generate a professional summary from personal info.

        Args:
            personal: Dictionary containing personal information

        Returns:
            Generated professional summary
        """
        pass

    @abstractmethod
    def improve_summary(self, summary: str) -> str:
        """Improve an existing summary.

        Args:
            summary: The original summary to improve

        Returns:
            Improved summary text
        """
        pass

    @abstractmethod
    def improve_experience(
        self, description: str, position: Optional[str] = None, company: Optional[str] = None
    ) -> str:
        """Improve experience description.

        Args:
            description: The original experience description
            position: Job position title
            company: Company name

        Returns:
            Improved experience description
        """
        pass

    @abstractmethod
    def improve_project(self, description: str, name: Optional[str] = None) -> str:
        """Improve project description.

        Args:
            description: The original project description
            name: Project name

        Returns:
            Improved project description
        """
        pass

    @abstractmethod
    def suggest_skills(
        self,
        current_skills: List[str],
        job_title: Optional[str] = None,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Suggest relevant skills.

        Args:
            current_skills: List of current skills
            job_title: Target job title
            job_description: Target job description

        Returns:
            Dictionary with suggested skills and categories
        """
        pass

    @abstractmethod
    def analyze_resume(self, resume: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a resume and provide feedback.

        Args:
            resume: Resume data dictionary

        Returns:
            Dictionary with analysis results
        """
        pass

    @abstractmethod
    def generate_cover_letter(
        self,
        personal: Dict[str, Any],
        job_title: str,
        company_name: str,
        job_description: Optional[str] = None,
        tone: str = "professional",
    ) -> str:
        """Generate a cover letter.

        Args:
            personal: Personal information dictionary
            job_title: Target job title
            company_name: Target company name
            job_description: Job description
            tone: Tone (professional, friendly, executive, creative)

        Returns:
            Generated cover letter content
        """
        pass

    @abstractmethod
    def improve_cover_letter(
        self,
        content: str,
        action: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> str:
        """Improve/edit a cover letter.

        Args:
            content: Original cover letter content
            action: Action (improve, rewrite, shorten, expand, grammar_fix, ats_optimize)
            job_title: Target job title
            company_name: Target company name

        Returns:
            Edited cover letter content
        """
        pass