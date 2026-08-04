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

    @abstractmethod
    def generate_cold_email(
        self,
        recipient_name: Optional[str] = None,
        recipient_role: Optional[str] = None,
        recipient_company: Optional[str] = None,
        tone: str = "professional",
        custom_context: Optional[str] = None,
        resume_summary: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate a cold outreach email.

        Args:
            recipient_name: Name of the recipient
            recipient_role: Role/title of the recipient
            recipient_company: Company name
            tone: Tone (professional, friendly, executive, creative)
            custom_context: Additional context from the user
            resume_summary: Optional resume summary for personalization

        Returns:
            Dict with 'subject' and 'body' keys
        """
        pass

    @abstractmethod
    def generate_follow_up(
        self,
        recipient_name: Optional[str] = None,
        recipient_company: Optional[str] = None,
        tone: str = "professional",
        custom_context: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate a follow-up email after an application.

        Args:
            recipient_name: Name of the recipient
            recipient_company: Company name
            tone: Tone (professional, friendly, executive, creative)
            custom_context: Additional context from the user

        Returns:
            Dict with 'subject' and 'body' keys
        """
        pass

    @abstractmethod
    def generate_thank_you(
        self,
        recipient_name: Optional[str] = None,
        recipient_company: Optional[str] = None,
        tone: str = "professional",
        custom_context: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate a post-interview thank-you note.

        Args:
            recipient_name: Name of the recipient
            recipient_company: Company name
            tone: Tone (professional, friendly, executive, creative)
            custom_context: Additional context from the user

        Returns:
            Dict with 'subject' and 'body' keys
        """
        pass

    @abstractmethod
    def generate_linkedin_note(
        self,
        recipient_name: Optional[str] = None,
        recipient_role: Optional[str] = None,
        recipient_company: Optional[str] = None,
        tone: str = "professional",
        custom_context: Optional[str] = None,
        resume_summary: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate a short LinkedIn connection note (max ~300 chars).

        Args:
            recipient_name: Name of the recipient
            recipient_role: Role/title of the recipient
            recipient_company: Company name
            tone: Tone (professional, friendly, executive, creative)
            custom_context: Additional context from the user
            resume_summary: Optional resume summary for personalization

        Returns:
            Dict with 'subject' (empty) and 'body' keys
        """
        pass

    @abstractmethod
    def generate_recruiter_reply(
        self,
        inbound_message: str,
        reply_intent: str,
        recipient_name: Optional[str] = None,
        recipient_company: Optional[str] = None,
        tone: str = "professional",
        custom_context: Optional[str] = None,
        thread_context: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, str]:
        """Generate a reply to an inbound recruiter message.

        Args:
            inbound_message: The original message from the recruiter
            reply_intent: The candidate's intent (accept_interest, decline_politely,
                         negotiate_timing, ask_clarifying_questions)
            recipient_name: Name of the recruiter (optional)
            recipient_company: Company name (optional)
            tone: Tone (professional, friendly, executive, creative)
            custom_context: Additional context from the user
            thread_context: Optional prior messages from the application's thread
                            (list of dicts with direction/sender/body/etc.) to give
                            the reply full conversational context.

        Returns:
            Dict with 'subject' and 'body' keys
        """
        pass

    @abstractmethod
    def generate_referral_request(
        self,
        recipient_name: Optional[str] = None,
        recipient_role: Optional[str] = None,
        recipient_company: Optional[str] = None,
        tone: str = "professional",
        custom_context: Optional[str] = None,
        resume_summary: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate a referral request message.

        Args:
            recipient_name: Name of the recipient
            recipient_role: Role/title of the recipient
            recipient_company: Company name
            tone: Tone (professional, friendly, executive, creative)
            custom_context: Additional context from the user
            resume_summary: Optional resume summary for personalization

        Returns:
            Dict with 'subject' and 'body' keys
        """
        pass

    @abstractmethod
    def generate_answer_evaluation(
        self,
        question: str,
        answer: str,
        job_title: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate an interview answer.

        Args:
            question: The interview question
            answer: The candidate's answer
            job_title: Optional job title for context
            difficulty: Optional difficulty level

        Returns:
            Dict with either an "evaluation" key (containing score, strengths,
            improvements, model_answer_notes) or an "evaluation_failed" key (true)
        """
        pass

    @abstractmethod
    def generate_interview_questions(
        self,
        job_title: str,
        job_role: Optional[str] = None,
        skills: Optional[List[str]] = None,
        difficulty: str = "medium",
        question_count: int = 5,
        company: Optional[str] = None,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate realistic interview questions for a given role/skills.

        Args:
            job_title: The target job title
            job_role: Optional broader role category
            skills: List of relevant skills
            difficulty: "easy", "medium", or "hard"
            question_count: Number of questions to generate (1-20)
            company: Optional company name for context
            job_description: Optional job description text for context

        Returns:
            Dict with a "questions" key containing a list of question dicts
        """
        pass