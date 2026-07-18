"""Gemini AI Provider implementation."""
import json
import logging
import time
from typing import List, Dict, Any, Optional

from google.api_core.exceptions import TooManyRequests, GoogleAPICallError
from google.genai import Client
from google.genai.errors import ClientError


from app.core.config import settings
from app.providers.base import AIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """AI Provider using Google's Gemini API (google-genai SDK v0.5.x)."""

    def __init__(self):
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        self.model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"
        # google-genai client
        self.client = Client(api_key=api_key)
        logger.info(f"Initialized Gemini provider with model: {self.model_name}")

    def _extract_response_text(self, response: Any) -> str:
        """
        google-genai response shape differs slightly across versions.
        Try common fields and fall back to stringifying.
        """
        if response is None:
            return ""

        # Most common: response.text
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        # Some SDK versions expose model_output (or similar)
        model_output = getattr(response, "model_output", None)
        if model_output is not None:
            mo_text = getattr(model_output, "text", None)
            if isinstance(mo_text, str) and mo_text.strip():
                return mo_text.strip()

        # Last resort: try dict-style access
        if isinstance(response, dict):
            for key in ("text", "output", "model_output"):
                val = response.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()

                if isinstance(val, dict):
                    t2 = val.get("text")
                    if isinstance(t2, str) and t2.strip():
                        return t2.strip()

        # Fallback string conversion
        try:
            s = str(response)
            return s.strip()
        except Exception:
            return ""

    def _generate_content(self, prompt: str, max_retries: int = 2) -> str:
        """
        Generate content with retry logic for transient errors.
        Uses google-genai SDK call patterns compatible with v0.5.0.
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )

                text = self._extract_response_text(response)
                if text:
                    return text

                last_error = ValueError("Empty response from Gemini API")
            except TooManyRequests as e:
                logger.warning(
                    f"Rate limit exceeded (attempt {attempt + 1}/{max_retries + 1})"
                )
                last_error = e
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
            except GoogleAPICallError as e:
                logger.error(f"Gemini API error: {e}")

                # google-genai v0.5.x raises 429 as google.genai.errors.ClientError
                # with status_code in the exception.
                status_code = getattr(e, "status_code", None)

                # Resource exhausted/quota exceeded
                if status_code == 429 or "RESOURCE_EXHAUSTED" in str(e).upper():
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
                        last_error = e
                        continue
                    # Raise so FastAPI can map it; handled globally as AppException
                    from app.utils.exceptions import AppException
                    raise AppException(
                        status_code=429,
                        message="Gemini quota exceeded. Please retry later.",
                    )

                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    last_error = e
                    continue
                raise
            except ClientError as e:
                logger.error(f"Gemini client error: {e}")
                status_code = getattr(e, "status_code", None)
                if status_code == 429 or "RESOURCE_EXHAUSTED" in str(e).upper():
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
                        last_error = e
                        continue
                    from app.utils.exceptions import AppException
                    raise AppException(
                        status_code=429,
                        message="Gemini quota exceeded. Please retry later.",
                    )

                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    last_error = e
                    continue
                raise



        if last_error:
            raise last_error
        return ""

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from the model's response.

        Args:
            response: Raw response text from the model

        Returns:
            Parsed JSON as a dictionary
        """
        # Try to find JSON in the response
        json_start = response.find("{")
        json_end = response.rfind("}")

        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = response[json_start : json_end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Return as-is if not valid JSON
        return {"error": "Failed to parse response", "raw": response}

    def generate_summary(self, personal: Dict[str, Any]) -> str:
        """Generate a professional summary from personal info."""
        from app.prompts.summary import generate_summary_prompt

        prompt = generate_summary_prompt(personal)
        return self._generate_content(prompt)

    def improve_summary(self, summary: str) -> str:
        """Improve an existing summary."""
        from app.prompts.summary import improve_summary_prompt

        prompt = improve_summary_prompt(summary)
        return self._generate_content(prompt)

    def improve_experience(
        self, description: str, position: Optional[str] = None, company: Optional[str] = None
    ) -> str:
        """Improve experience description."""
        from app.prompts.experience import improve_experience_prompt

        prompt = improve_experience_prompt(description, position, company)
        return self._generate_content(prompt)

    def improve_project(self, description: str, name: Optional[str] = None) -> str:
        """Improve project description."""
        from app.prompts.project import improve_project_prompt

        prompt = improve_project_prompt(description, name)
        return self._generate_content(prompt)

    def suggest_skills(
        self,
        current_skills: List[str],
        job_title: Optional[str] = None,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Suggest relevant skills."""
        from app.prompts.skills import suggest_skills_prompt

        prompt = suggest_skills_prompt(current_skills, job_title, job_description)
        response = self._generate_content(prompt)

        # Try to parse as JSON
        try:
            result = self._parse_json_response(response)
            if "skills" in result:
                return result
        except Exception as e:
            logger.warning(f"Failed to parse skills response as JSON: {e}")

        # Fallback: extract skills from text
        skills = [s.strip() for s in response.replace("\n", ",").split(",") if s.strip()]
        return {
            "skills": skills[:10],
            "categories": {},
        }

    def analyze_resume(self, resume: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a resume and provide feedback."""
        from app.prompts.analysis import analyze_resume_prompt

        prompt = analyze_resume_prompt(resume)
        response = self._generate_content(prompt)

        # Try to parse as JSON
        try:
            result = self._parse_json_response(response)
            if "resume_score" in result:
                return result
        except Exception as e:
            logger.warning(f"Failed to parse analysis response as JSON: {e}")

        # Return fallback structure
        return {
            "resume_score": 70,
            "ats_score": 75,
            "suggestions": ["Unable to analyze resume properly"],
            "strengths": ["Resume structure present"],
            "weaknesses": ["Analysis incomplete"],
        }

    def generate_cover_letter(
        self,
        personal: Dict[str, Any],
        job_title: str,
        company_name: str,
        job_description: Optional[str] = None,
        tone: str = "professional",
    ) -> str:
        """Generate a cover letter.

        Note: Cover-letter prompt builders live in `app/routers/cover_letter.py` today.
        This provider implements a minimal prompt here to satisfy the BaseProvider contract.
        """

        resume_text = ""
        if personal:
            # Try to reuse the same resume_data structure used elsewhere in the app.
            pi = personal.get("personal_info") or personal.get("personal") or {}
            if pi:
                resume_text += f"Name: {pi.get('name', '')}\n"
                resume_text += f"Email: {pi.get('email', '')}\n"
                resume_text += f"Phone: {pi.get('phone', '')}\n"
                resume_text += f"Location: {pi.get('location', '')}\n\n"

            if personal.get("summary"):
                resume_text += f"Summary: {personal.get('summary', '')}\n\n"

            exp = personal.get("experience")
            if exp:
                resume_text += "Experience:\n"
                for e in exp:
                    resume_text += (
                        f"- {e.get('title', '')} at {e.get('company', '')} "
                        f"({e.get('start_date', '')} - {e.get('end_date', '')}): {e.get('description', '')}\n"
                    )
                resume_text += "\n"

            skills = personal.get("skills")
            if skills:
                resume_text += f"Skills: {', '.join(skills)}\n\n"

            education = personal.get("education")
            if education:
                resume_text += "Education:\n"
                for edu in education:
                    resume_text += (
                        f"- {edu.get('degree', '')} at {edu.get('institution', '')} ({edu.get('year', '')})\n"
                    )
                resume_text += "\n"

        prompt = f"""Write a {tone} cover letter for a job application.

Job Title: {job_title}
Company: {company_name}
"""
        if job_description:
            prompt += f"Job Description: {job_description}\n\n"
        if resume_text.strip():
            prompt += f"Candidate Resume:\n{resume_text}\n"

        prompt += """
Write a compelling cover letter that:
1. Addresses the hiring manager professionally
2. Highlights relevant skills and experience
3. Explains why the candidate is a great fit for this role
4. Has a strong closing statement

Keep it concise (250-400 words) and ATS-friendly. Use standard business letter format.
"""

        return self._generate_content(prompt)

    def improve_cover_letter(
        self,
        content: str,
        action: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> str:
        """Edit a cover letter.

        Provides minimal implementations for the actions supported by the cover-letter routes.
        """

        content = content or ""
        job_ctx = ""
        if job_title and company_name:
            job_ctx = f"For {job_title} at {company_name}"

        prompt = ""
        if action == "improve":
            prompt = (
                "Improve this cover letter to make it more compelling and professional:\n\n"
                f"{content}\n\n{job_ctx}\n\nMake it more impactful while keeping the same length."
            )
        elif action == "rewrite":
            prompt = (
                "Rewrite this cover letter with a fresh perspective:\n\n"
                f"{content}\n\n{job_ctx}\n\nKeep it professional and engaging."
            )
        elif action == "shorten":
            prompt = (
                "Shorten this cover letter while keeping the key points:\n\n"
                f"{content}\n\nReduce to ~150-200 words. Keep the essential message."
            )
        elif action == "expand":
            prompt = (
                "Expand this cover letter with more detail:\n\n"
                f"{content}\n\nAdd more specific examples and details (350-450 words)."
            )
        elif action == "grammar_fix":
            prompt = (
                "Fix any grammar, spelling, and punctuation errors in this cover letter:\n\n"
                f"{content}\n\nReturn the corrected version."
            )
        elif action == "ats_optimize":
            prompt = (
                "Optimize this cover letter for ATS systems (Applicant Tracking Systems):\n\n"
                f"{content}\n\n"
                "- Include relevant keywords from the job description if present in the letter\n"
                "- Use standard formatting\n"
                "- Avoid tables, images, or special characters\n"
                "- Keep it simple and text-based"
            )
        else:
            prompt = f"{content}"

        return self._generate_content(prompt)


