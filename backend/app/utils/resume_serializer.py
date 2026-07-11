import json


def _parse_json(value, default):
    if value is None:
        return default

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return default


def serialize_resume(resume):
    print(">>> serialize_resume() called")
    return {
        "id": resume.id,
        "user_id": resume.user_id,
        "name": resume.name,

        "personal": _parse_json(resume.personal, {}),
        "summary": resume.summary,

        "experience": _parse_json(resume.experience, []),
        "education": _parse_json(resume.education, []),
        "skills": _parse_json(resume.skills, []),
        "projects": _parse_json(resume.projects, []),
        "certifications": _parse_json(resume.certifications, []),
        "languages": _parse_json(resume.languages, []),
        "interests": _parse_json(resume.interests, []),
        "references": _parse_json(resume.references, []),

        "is_default": resume.is_default,
        "is_archived": resume.is_archived,
        "completed": getattr(resume, "completed", False),
        "version": resume.version,


        "created_at": resume.created_at,
        "updated_at": resume.updated_at,
    }