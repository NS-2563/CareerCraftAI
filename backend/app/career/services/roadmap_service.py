import logging
from copy import deepcopy
from datetime import datetime
from unittest import result

from app.ai.context_builder import build_context
from app.ai.ai_engine import generate_json
from app.ai.prompt_builder import PromptBuilder

from app.career.services.learning_path import generate_learning_path
from app.career.services.suggestions import generate_suggestions

from app.career.services.career_readiness import calculate_career_readiness
from app.career.services.employability import predict_employability


logger = logging.getLogger(__name__)


CAREER_REPORT_SCHEMA = {

    "career_goal": "",

    "readiness_score": 0,

    "readiness_status": "",

    "best_match": "",

    "career_summary": "",


    "strengths": [],

    "weaknesses": [],


    "career_paths": [
        {
            "title": "",
            "reason": "",
            "difficulty": "",
            "future_demand": ""
        }
    ],


    "skill_gap": {

        "existing_skills": [],

        "missing_skills": [],

        "priority": []
    },


    "roadmap": [

        {
            "stage": "",

            "topics": [],

            "projects": []
        }

    ],


    "action_plan": {

        "next_week": [],

        "next_month": [],

        "next_6_months": []
    },


    "resources": [

        {
            "title": "",

            "type": "",

            "description": ""
        }

    ],

}


def normalize_skills(raw_skills):
    """
    Convert skills input into a clean list.
    """

    if isinstance(raw_skills, list):
        return [
            str(skill).strip()
            for skill in raw_skills
            if str(skill).strip()
        ]

    return [
        skill.strip()
        for skill in str(raw_skills).split(",")
        if skill.strip()
    ]


def build_fallback_report(data: dict, db=None, user_id: int = None) -> dict:
    """
    Generate deterministic career report
    when AI generation fails.
    """

    skills = normalize_skills(
        data.get("skills", "")
    )

    roadmap = generate_learning_path(
        skills
    )

    suggestions = generate_suggestions(
        missing_skills=skills,
        sections_found={
            "skills": bool(skills),
            "projects": False,
            "certifications": False,
            "experience": bool(
                data.get("experience")
            ),
            "summary": False,
        },
    )

    readiness = calculate_career_readiness(
        ats_score=50,
        skill_match=50,
        sections_found={
            "projects": False,
            "certifications": False,
        }
    )


    employability = predict_employability(
        ats_score=50,
        skills_count=len(skills),
        completeness_score=50,
    )


    report = deepcopy(
        CAREER_REPORT_SCHEMA
    )


    report.update(
        {
            "career_goal": data.get(
                "goal",
                ""
            ),

            "generated_at": datetime.utcnow().isoformat(),

            "readiness_score": readiness[
                "career_readiness_score"
            ],

            "readiness_status": readiness[
                "status"
            ],

            "best_match": data.get(
                "goal",
                "Career Path Analysis"
            ),

            "career_summary": (
                "This report was generated "
                "using CareerCraft fallback "
                "intelligence because AI "
                "generation was unavailable."
            ),

            "strengths": skills,

            "weaknesses": suggestions,

            "career_paths": [
                {
                    "title": data.get(
                        "goal",
                        "Software Development"
                    ),
                    "reason": (
                        "Matches candidate "
                        "interest and skills."
                    ),
                    "difficulty": "Intermediate",
                    "future_demand": "High",
                }
            ],

            "skill_gap": {
                "existing_skills": skills,
                "missing_skills": [],
                "priority": skills[:3],
            },

            "roadmap": [
    {
        "stage": "Foundation",
        "topics": skills,
        "projects": [
            "Build a practical project using learned skills"
        ]
    }
],

            "action_plan": {
                "next_week": suggestions[:3],
                "next_month": roadmap,
                "next_6_months": [],
            },

            "resources": [
    {
        "title": "Learning Resources",
        "type": "Course",
        "description": "Follow structured courses and official documentation."
    }
],

            "employability": employability,
        }
    )

    if db is not None and user_id is not None:
        from app.career.services.recommendation_signals import (
            enrich_priority_recommendations,
        )
        report["skill_gap"]["priority"] = enrich_priority_recommendations(
            report, db, user_id
        )

    return report



def generate_career_report(data: dict, db=None, user_id: int = None) -> dict:
    """
    AI-first career report generator
    with deterministic fallback.
    """

    if not isinstance(data, dict):
        data = {}

    context = build_context(
        module="Career Coach",
        user_data=data,
        db=db,
        user_id=user_id,
    )

    prompt = (
        PromptBuilder()
        .set_system(
            "You are CareerCraft AI, an expert career mentor."
        )
        .set_context(context)
        .set_task(
            """
Analyze the candidate profile.

Generate a career guidance report.

Rules:

Career Paths:
Return a list of objects.
Each object must contain:
- title
- reason
- difficulty
- future_demand

Skill Gap:
Return:
- existing_skills
- missing_skills
- priority

IMPORTANT:
- existing_skills MUST contain ONLY the skills explicitly provided by the user.
- Never infer or add additional existing skills.
- Do not add HTML, CSS, JavaScript, Git, SQL or any other technology unless explicitly provided.

REAL USER SIGNALS:
The CONTEXT may include a "Real User Signals" section computed from the user's
own data (saved JD match results, interview practice sessions, and real
interview logs). If present, ground your Skill Gap, Learning Roadmap, and
Action Plan recommendations in these signals:

- "Skill gaps from the user's own saved JD matches" lists skills that are
  required by jobs the user has actually applied to and are missing from their
  resume. Prioritize the most frequent of these in missing_skills and roadmap
  topics.
- "Weakest interview category" lists the category with the lowest average
  practice score. Reflect it in roadmap topics and action plan items so the
  user can strengthen that area.
- "Real interview logs" list how the user's actual interviews went, with
  self-rated confidence and notes. A real interview outcome is more
  informative than practice performance: when both a real interview log and
  practice scores exist for the same area, weight the real interview signal
  more heavily in your recommendations.

When these signals are NOT present (e.g. a new user with no saved matches or
no interview sessions yet), fall back to the resume-based approach using only
the profile data above. Never invent the signals; only use them when they are
explicitly listed in the context.

Learning Roadmap:
Return a list of stages.
Each stage must contain:
- stage
- topics
- projects

Action Plan:
Return exactly:
- next_week
- next_month
- next_6_months

Resources:
Return objects containing:
- title
- type
- description

Return only valid JSON.
"""
        )
        .set_schema(CAREER_REPORT_SCHEMA)
        .build()
    )

    try:

        result = generate_json(
            prompt=prompt,
            schema=CAREER_REPORT_SCHEMA
        )

        if result.get("success"):

            logger.info(
                "Career report generated using AI."
            )

            result["source"] = "ai"

            # Keep user-provided skills authoritative
            skills = normalize_skills(
                data.get("skills", "")
            )

            skill_gap = result["data"].get(
                "skill_gap",
                {}
            )

            if not isinstance(skill_gap, dict):
                skill_gap = {}

            skill_gap["existing_skills"] = skills
            skill_gap.setdefault("missing_skills", [])
            skill_gap.setdefault("priority", [])

            if db is not None and user_id is not None:
                from app.career.services.recommendation_signals import (
                    enrich_priority_recommendations,
                )
                skill_gap["priority"] = enrich_priority_recommendations(
                    result["data"], db, user_id
                )

            result["data"]["skill_gap"] = skill_gap

            if "generated_at" not in result["data"]:
                result["data"]["generated_at"] = datetime.utcnow().isoformat()
            return result

        logger.warning(
            "AI returned invalid response."
        )

    except Exception as error:

        logger.exception(
            "Career AI generation failed: %s",
            error
        )

    logger.warning(
        "Switching to fallback career engine."
    )

    return {
        "success": True,
        "data": build_fallback_report(data, db=db, user_id=user_id),
        "source": "fallback",
    }