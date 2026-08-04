from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.resume import Resume
from app.schemas.resume import ResumeCreate, ResumeUpdate
from app.utils.exceptions import NotFoundException
from app.utils.json_utils import to_json, from_json
from app.utils.versioned import create_version_snapshot, get_version_history, record_version, find_version
from app.activity.service import ActivityService
from app.activity.constants import EventType


def _get_all_fields_json(resume: Resume) -> dict:
    """Get all resume fields as dict."""
    return {
        "personal": resume.personal,
        "summary": resume.summary,
        "experience": resume.experience,
        "education": resume.education,
        "skills": resume.skills,
        "projects": resume.projects,
        "certifications": resume.certifications,
        "languages": resume.languages,
        "interests": resume.interests,
        "references": resume.references,
    }


class ResumeService:
    """Service for resume CRUD operations."""

    @staticmethod
    def create(db: Session, user_id: int, resume_data: ResumeCreate) -> Resume:
        """Create a new resume."""
        resume = Resume(
            user_id=user_id,
            name=resume_data.name,
            completed=getattr(resume_data, "completed", False),

            personal=to_json(resume_data.personal.model_dump() if resume_data.personal else None),
            summary=resume_data.summary,
            experience=to_json([e.model_dump() for e in resume_data.experience] if resume_data.experience else []),
            education=to_json([e.model_dump() for e in resume_data.education] if resume_data.education else []),
            skills=to_json([s.model_dump() for s in resume_data.skills] if resume_data.skills else []),
            projects=to_json([p.model_dump() for p in resume_data.projects] if resume_data.projects else []),
            certifications=to_json([c.model_dump() for c in resume_data.certifications] if resume_data.certifications else []),
            languages=to_json([l.model_dump() for l in resume_data.languages] if resume_data.languages else []),
            interests=to_json([i.model_dump() for i in resume_data.interests] if resume_data.interests else []),
            references=to_json([r.model_dump() for r in resume_data.references] if resume_data.references else []),
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        ActivityService.log_event(
            db, user_id, EventType.RESUME_CREATED,
            title="Resume created",
            description=resume.name,
            related_entity_type="resume",
            related_entity_id=resume.id,
        )
        return resume

    @staticmethod
    def get_by_id(db: Session, resume_id: int, user_id: int) -> Resume:
        """Get resume by ID."""
        resume = db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        ).first()
        if not resume:
            raise NotFoundException("Resume", str(resume_id))
        return resume

    @staticmethod
    def get_all(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    archived: bool | None = None,
    ) -> List[Resume]:
        """Get resumes for a user."""

        query = db.query(Resume).filter(
            Resume.user_id == user_id
        )

        if archived is not None:
            query = query.filter(Resume.is_archived == archived)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, resume_id: int, user_id: int, resume_data: ResumeUpdate) -> Resume:
        """Update an existing resume."""
        resume = ResumeService.get_by_id(db, resume_id, user_id)

        # Create version snapshot before updating
        snapshot = create_version_snapshot(resume, _get_all_fields_json(resume), "Before update")
        record_version(resume, snapshot)

        # Update fields
        update_data = resume_data.model_dump(exclude_unset=True)

        if "name" in update_data and update_data["name"]:
            resume.name = update_data["name"]
        if "completed" in update_data and update_data["completed"] is not None:
            resume.completed = bool(update_data["completed"])
        if "summary" in update_data and update_data["summary"] is not None:
            resume.summary = update_data["summary"]

        # Handle nested objects - convert to JSON strings
        if "personal" in update_data and update_data["personal"]:
            resume.personal = to_json(update_data["personal"].model_dump() if hasattr(update_data["personal"], "model_dump") else update_data["personal"])
        if "experience" in update_data and update_data["experience"] is not None:
            resume.experience = to_json([e.model_dump() if hasattr(e, "model_dump") else e for e in update_data["experience"]])
        if "education" in update_data and update_data["education"] is not None:
            resume.education = to_json([e.model_dump() if hasattr(e, "model_dump") else e for e in update_data["education"]])
        if "skills" in update_data and update_data["skills"] is not None:
            resume.skills = to_json([s.model_dump() if hasattr(s, "model_dump") else s for s in update_data["skills"]])
        if "projects" in update_data and update_data["projects"] is not None:
            resume.projects = to_json([p.model_dump() if hasattr(p, "model_dump") else p for p in update_data["projects"]])
        if "certifications" in update_data and update_data["certifications"] is not None:
            resume.certifications = to_json([c.model_dump() if hasattr(c, "model_dump") else c for c in update_data["certifications"]])
        if "languages" in update_data and update_data["languages"] is not None:
            resume.languages = to_json([l.model_dump() if hasattr(l, "model_dump") else l for l in update_data["languages"]])
        if "interests" in update_data and update_data["interests"] is not None:
            resume.interests = to_json([i.model_dump() if hasattr(i, "model_dump") else i for i in update_data["interests"]])
        if "references" in update_data and update_data["references"] is not None:
            resume.references = to_json([r.model_dump() if hasattr(r, "model_dump") else r for r in update_data["references"]])

        # Increment version
        resume.version += 1

        db.commit()
        db.refresh(resume)
        ActivityService.log_event(
            db, user_id, EventType.RESUME_UPDATED,
            title="Resume updated",
            description=resume.name or "Untitled resume",
            related_entity_type="resume",
            related_entity_id=resume.id,
        )
        return resume

    @staticmethod
    def delete(db: Session, resume_id: int, user_id: int) -> None:
        """Delete a resume."""
        resume = ResumeService.get_by_id(db, resume_id, user_id)
        db.delete(resume)
        db.commit()
        ActivityService.log_event(
            db, user_id, EventType.RESUME_DELETED,
            title="Resume deleted",
            description=resume.name or "Untitled resume",
        )

    @staticmethod
    def duplicate(db: Session, resume_id: int, user_id: int, new_name: str) -> Resume:
        """Duplicate a resume."""
        original = ResumeService.get_by_id(db, resume_id, user_id)

        new_resume = Resume(
            user_id=user_id,
            name=new_name,
            personal=original.personal,
            summary=original.summary,
            experience=original.experience,
            education=original.education,
            skills=original.skills,
            projects=original.projects,
            certifications=original.certifications,
            languages=original.languages,
            interests=original.interests,
            references=original.references,
            version=1,
            version_history="[]",
        )
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        ActivityService.log_event(
            db, user_id, EventType.RESUME_DUPLICATED,
            title="Resume duplicated",
            description=f"{original.name} → {new_resume.name}",
            related_entity_type="resume",
            related_entity_id=new_resume.id,
        )
        return new_resume

    @staticmethod
    def rename(db: Session, resume_id: int, user_id: int, new_name: str) -> Resume:
        """Rename a resume."""
        resume = ResumeService.get_by_id(db, resume_id, user_id)
        resume.name = new_name
        db.commit()
        db.refresh(resume)
        return resume

    @staticmethod
    def get_version_history(db: Session, resume_id: int, user_id: int) -> List[dict]:
        """Get version history."""
        resume = ResumeService.get_by_id(db, resume_id, user_id)
        return get_version_history(resume.version_history)

    @staticmethod
    def archive(db: Session, resume_id: int, user_id: int) -> Resume:
        """Archive a resume."""
        resume = ResumeService.get_by_id(db, resume_id, user_id)
        resume.is_archived = True
        db.commit()
        db.refresh(resume)
        return resume

    @staticmethod
    def restore(db: Session, resume_id: int, user_id: int) -> Resume:
        """Restore an archived resume."""
        resume = ResumeService.get_by_id(db, resume_id, user_id)
        resume.is_archived = False
        db.commit()
        db.refresh(resume)
        return resume

    @staticmethod
    def get_archived(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Resume]:
        """Get all archived resumes for a user."""
        return db.query(Resume).filter(
            Resume.user_id == user_id,
            Resume.is_archived == True,
        ).offset(skip).limit(limit).all()

    @staticmethod
    def search(db: Session, user_id: int, query: str, include_archived: bool = False) -> List[Resume]:
        """Search resumes by name, skills, companies, or education."""
        base_query = db.query(Resume).filter(Resume.user_id == user_id)

        if not include_archived:
            base_query = base_query.filter(Resume.is_archived == False)

        resumes = base_query.all()

        # Filter locally for more complex search
        if query:
            query_lower = query.lower()
            results = []
            for resume in resumes:
                # Search in name
                if query_lower in resume.name.lower():
                    results.append(resume)
                    continue

                # Search in skills
                if resume.skills and query_lower in resume.skills.lower():
                    results.append(resume)
                    continue

                # Search in experience (companies)
                if resume.experience and query_lower in resume.experience.lower():
                    results.append(resume)
                    continue

                # Search in education (institutions)
                if resume.education and query_lower in resume.education.lower():
                    results.append(resume)
                    continue

            return results

        return resumes

    @staticmethod
    def get_all_sorted(
        db: Session,
        user_id: int,
        sort_by: str = "updated_at",
        include_archived: bool = False,
    ) -> List[Resume]:
        """Get all resumes sorted."""
        query = db.query(Resume).filter(Resume.user_id == user_id)

        if not include_archived:
            query = query.filter(Resume.is_archived == False)

        if sort_by == "name":
            return query.order_by(Resume.name).all()
        elif sort_by == "created_at":
            return query.order_by(Resume.created_at.desc()).all()
        elif sort_by == "updated_at":
            return query.order_by(Resume.updated_at.desc()).all()
        else:
            return query.order_by(Resume.updated_at.desc()).all()

    @staticmethod
    def restore_version(db: Session, resume_id: int, user_id: int, version: int) -> Resume:
        """Restore a specific version of the resume."""
        resume = ResumeService.get_by_id(db, resume_id, user_id)
        history = get_version_history(resume.version_history)

        # Find the version snapshot
        target = find_version(history, version)

        if not target:
            raise NotFoundException(f"Version {version}", "not found")

        data = target.get("data", {})

        # Create snapshot before restoring
        snapshot = create_version_snapshot(resume, _get_all_fields_json(resume), f"Before restore to v{version}")
        record_version(resume, snapshot)

        # Restore data
        if "personal" in data:
            resume.personal = data["personal"]
        if "summary" in data:
            resume.summary = data["summary"]
        if "experience" in data:
            resume.experience = data["experience"]
        if "education" in data:
            resume.education = data["education"]
        if "skills" in data:
            resume.skills = data["skills"]
        if "projects" in data:
            resume.projects = data["projects"]
        if "certifications" in data:
            resume.certifications = data["certifications"]
        if "languages" in data:
            resume.languages = data["languages"]
        if "interests" in data:
            resume.interests = data["interests"]
        if "references" in data:
            resume.references = data["references"]

        resume.version += 1

        db.commit()
        db.refresh(resume)
        return resume
