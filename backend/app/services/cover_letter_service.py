from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.cover_letter import CoverLetter
from app.models.resume import Resume
from app.schemas.cover_letter import CoverLetterCreate, CoverLetterUpdate
from app.utils.exceptions import NotFoundException
from app.utils.json_utils import to_json, from_json
from app.utils.versioned import create_version_snapshot, get_version_history, record_version, find_version
from app.activity.service import ActivityService
from app.activity.constants import EventType


def check_generation_prerequisites(
    resume_id: Optional[int],
    job_title: Optional[str],
    company_name: Optional[str],
    job_description: Optional[str],
) -> list:
    """Return the list of missing generation inputs (empty when ready).

    Deterministic presence check only — mirrors the inputs the generation
    endpoints consume so the client can surface exactly what is missing before
    an AI call is attempted. Returns normalized keys: ``"resume"``,
    ``"job title"``, ``"company name"``, ``"job description"``.
    """
    missing = []
    if not resume_id:
        missing.append("resume")
    if not (job_title or "").strip():
        missing.append("job title")
    if not (company_name or "").strip():
        missing.append("company name")
    if not (job_description or "").strip():
        missing.append("job description")
    return missing


def _get_all_fields_json(cover_letter: CoverLetter) -> dict:
    """Get all cover letter fields as dict."""
    return {
        "title": cover_letter.title,
        "content": cover_letter.content,
        "job_title": cover_letter.job_title,
        "company_name": cover_letter.company_name,
        "job_description": cover_letter.job_description,
        "tone": cover_letter.tone,
        "template": cover_letter.template,
    }


class CoverLetterService:
    """Service for cover letter CRUD operations."""

    @staticmethod
    def create(db: Session, user_id: int, cover_letter_data: CoverLetterCreate) -> CoverLetter:
        """Create a new cover letter."""
        if cover_letter_data.resume_id is not None:
            resume = db.query(Resume).filter(
                Resume.id == cover_letter_data.resume_id,
                Resume.user_id == user_id,
            ).first()
            if not resume:
                raise NotFoundException("Resume", str(cover_letter_data.resume_id))
        if cover_letter_data.job_application_id is not None:
            CoverLetterService._verify_job_application(db, user_id, cover_letter_data.job_application_id)
        cover_letter = CoverLetter(
            user_id=user_id,
            resume_id=cover_letter_data.resume_id,
            job_application_id=cover_letter_data.job_application_id,
            title=cover_letter_data.title,
            content=cover_letter_data.content,
            job_title=cover_letter_data.job_title,
            company_name=cover_letter_data.company_name,
            job_description=cover_letter_data.job_description,
            tone=cover_letter_data.tone or "professional",
            template=cover_letter_data.template or "modern",
        )
        db.add(cover_letter)
        db.commit()
        db.refresh(cover_letter)
        ActivityService.log_event(
            db, user_id, EventType.COVER_LETTER_CREATED,
            title="Cover letter created",
            description=cover_letter.title,
            related_entity_type="cover_letter",
            related_entity_id=cover_letter.id,
            related_job_application_id=cover_letter.job_application_id,
        )
        return cover_letter

    @staticmethod
    def _verify_job_application(db: Session, user_id: int, job_application_id: int) -> None:
        """Verify the job application belongs to the user before linking.

        Mirrors CommunicationMessage's ownership-check pattern — never trust a
        client-supplied ID across module boundaries.
        """
        from app.models.job_application import JobApplication
        job = db.query(JobApplication).filter(
            JobApplication.id == job_application_id,
            JobApplication.user_id == user_id,
        ).first()
        if not job:
            raise NotFoundException("JobApplication", str(job_application_id))

    @staticmethod
    def get_by_id(db: Session, cover_letter_id: int, user_id: int) -> CoverLetter:
        """Get cover letter by ID."""
        cover_letter = db.query(CoverLetter).filter(
            CoverLetter.id == cover_letter_id,
            CoverLetter.user_id == user_id,
        ).first()
        if not cover_letter:
            raise NotFoundException("CoverLetter", str(cover_letter_id))
        return cover_letter

    @staticmethod
    def get_all(db: Session, user_id: int, resume_id: Optional[int] = None, job_application_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[CoverLetter]:
        """Get all cover letters for a user."""
        query = db.query(CoverLetter).filter(
            CoverLetter.user_id == user_id,
            CoverLetter.is_archived == False,
        )
        if resume_id:
            query = query.filter(CoverLetter.resume_id == resume_id)
        if job_application_id:
            query = query.filter(CoverLetter.job_application_id == job_application_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, cover_letter_id: int, user_id: int, cover_letter_data: CoverLetterUpdate) -> CoverLetter:
        """Update an existing cover letter."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)

        # Create version snapshot before updating
        snapshot = create_version_snapshot(cover_letter, _get_all_fields_json(cover_letter), "Before update")
        record_version(cover_letter, snapshot)

        # Update fields
        update_data = cover_letter_data.model_dump(exclude_unset=True)

        if "title" in update_data and update_data["title"]:
            cover_letter.title = update_data["title"]
        if "content" in update_data and update_data["content"] is not None:
            cover_letter.content = update_data["content"]
        if "job_title" in update_data and update_data["job_title"] is not None:
            cover_letter.job_title = update_data["job_title"]
        if "company_name" in update_data and update_data["company_name"] is not None:
            cover_letter.company_name = update_data["company_name"]
        if "job_description" in update_data and update_data["job_description"] is not None:
            cover_letter.job_description = update_data["job_description"]
        if "tone" in update_data and update_data["tone"]:
            cover_letter.tone = update_data["tone"]
        if "template" in update_data and update_data["template"]:
            cover_letter.template = update_data["template"]
        if "resume_id" in update_data and update_data["resume_id"] is not None:
            cover_letter.resume_id = update_data["resume_id"]
        if "job_application_id" in update_data and update_data["job_application_id"] is not None:
            CoverLetterService._verify_job_application(db, user_id, update_data["job_application_id"])
            cover_letter.job_application_id = update_data["job_application_id"]

        # Increment version
        cover_letter.version += 1

        db.commit()
        db.refresh(cover_letter)
        ActivityService.log_event(
            db, user_id, EventType.COVER_LETTER_UPDATED,
            title="Cover letter updated",
            description=cover_letter.title or "Untitled cover letter",
            related_entity_type="cover_letter",
            related_entity_id=cover_letter.id,
            related_job_application_id=cover_letter.job_application_id,
        )
        return cover_letter

    @staticmethod
    def delete(db: Session, cover_letter_id: int, user_id: int) -> None:
        """Delete a cover letter."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)
        title = cover_letter.title or "Untitled cover letter"
        job_application_id = cover_letter.job_application_id
        db.delete(cover_letter)
        db.commit()
        ActivityService.log_event(
            db, user_id, EventType.COVER_LETTER_DELETED,
            title="Cover letter deleted",
            description=title,
            related_entity_type="cover_letter",
            related_entity_id=cover_letter_id,
            related_job_application_id=job_application_id,
        )

    @staticmethod
    def duplicate(db: Session, cover_letter_id: int, user_id: int, new_title: str) -> CoverLetter:
        """Duplicate a cover letter."""
        original = CoverLetterService.get_by_id(db, cover_letter_id, user_id)

        new_cover_letter = CoverLetter(
            user_id=user_id,
            resume_id=original.resume_id,
            job_application_id=original.job_application_id,
            title=new_title,
            content=original.content,
            job_title=original.job_title,
            company_name=original.company_name,
            job_description=original.job_description,
            tone=original.tone,
            template=original.template,
            version=1,
            version_history="[]",
        )
        db.add(new_cover_letter)
        db.commit()
        db.refresh(new_cover_letter)
        ActivityService.log_event(
            db, user_id, EventType.COVER_LETTER_DUPLICATED,
            title="Cover letter duplicated",
            description=f"{original.title} → {new_cover_letter.title}",
            related_entity_type="cover_letter",
            related_entity_id=new_cover_letter.id,
            related_job_application_id=new_cover_letter.job_application_id,
        )
        return new_cover_letter

    @staticmethod
    def rename(db: Session, cover_letter_id: int, user_id: int, new_title: str) -> CoverLetter:
        """Rename a cover letter."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)
        cover_letter.title = new_title
        db.commit()
        db.refresh(cover_letter)
        return cover_letter

    @staticmethod
    def get_version_history(db: Session, cover_letter_id: int, user_id: int) -> List[dict]:
        """Get version history."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)
        return get_version_history(cover_letter.version_history)

    @staticmethod
    def get_version_content(db: Session, cover_letter_id: int, user_id: int, version: int) -> Optional[str]:
        """Return the content captured for a specific version, or None.

        The current version reads from the live column; historical versions
        read from the version-history snapshots. Returns ``None`` when the
        version is not found (caller decides 404 vs empty diff).
        """
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)
        if version == cover_letter.version:
            return cover_letter.content
        history = get_version_history(cover_letter.version_history)
        target = find_version(history, version)
        if not target:
            return None
        return target.get("data", {}).get("content")

    @staticmethod
    def archive(db: Session, cover_letter_id: int, user_id: int) -> CoverLetter:
        """Archive a cover letter."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)
        cover_letter.is_archived = True
        db.commit()
        db.refresh(cover_letter)
        return cover_letter

    @staticmethod
    def restore(db: Session, cover_letter_id: int, user_id: int) -> CoverLetter:
        """Restore an archived cover letter."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)
        cover_letter.is_archived = False
        db.commit()
        db.refresh(cover_letter)
        return cover_letter

    @staticmethod
    def get_archived(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[CoverLetter]:
        """Get all archived cover letters for a user."""
        return db.query(CoverLetter).filter(
            CoverLetter.user_id == user_id,
            CoverLetter.is_archived == True,
        ).offset(skip).limit(limit).all()

    @staticmethod
    def search(db: Session, user_id: int, query: str, include_archived: bool = False) -> List[CoverLetter]:
        """Search cover letters."""
        base_query = db.query(CoverLetter).filter(CoverLetter.user_id == user_id)

        if not include_archived:
            base_query = base_query.filter(CoverLetter.is_archived == False)

        cover_letters = base_query.all()

        # Filter locally for more complex search
        if query:
            query_lower = query.lower()
            results = []
            for cl in cover_letters:
                if query_lower in cl.title.lower():
                    results.append(cl)
                    continue
                if cl.job_title and query_lower in cl.job_title.lower():
                    results.append(cl)
                    continue
                if cl.company_name and query_lower in cl.company_name.lower():
                    results.append(cl)
                    continue
                if cl.content and query_lower in cl.content.lower():
                    results.append(cl)
                    continue

            return results

        return cover_letters

    @staticmethod
    def get_all_sorted(
        db: Session,
        user_id: int,
        sort_by: str = "updated_at",
        include_archived: bool = False,
    ) -> List[CoverLetter]:
        """Get all cover letters sorted."""
        query = db.query(CoverLetter).filter(CoverLetter.user_id == user_id)

        if not include_archived:
            query = query.filter(CoverLetter.is_archived == False)

        if sort_by == "title":
            return query.order_by(CoverLetter.title).all()
        elif sort_by == "created_at":
            return query.order_by(CoverLetter.created_at.desc()).all()
        elif sort_by == "updated_at":
            return query.order_by(CoverLetter.updated_at.desc()).all()
        else:
            return query.order_by(CoverLetter.updated_at.desc()).all()

    @staticmethod
    def restore_version(db: Session, cover_letter_id: int, user_id: int, version: int) -> CoverLetter:
        """Restore a specific version of the cover letter."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)
        history = get_version_history(cover_letter.version_history)

        # Find the version snapshot
        target = find_version(history, version)

        if not target:
            raise NotFoundException(f"Version {version}", "not found")

        data = target.get("data", {})

        # Create snapshot before restoring
        snapshot = create_version_snapshot(cover_letter, _get_all_fields_json(cover_letter), f"Before restore to v{version}")
        record_version(cover_letter, snapshot)

        # Restore data
        if "title" in data:
            cover_letter.title = data["title"]
        if "content" in data:
            cover_letter.content = data["content"]
        if "job_title" in data:
            cover_letter.job_title = data["job_title"]
        if "company_name" in data:
            cover_letter.company_name = data["company_name"]
        if "job_description" in data:
            cover_letter.job_description = data["job_description"]
        if "tone" in data:
            cover_letter.tone = data["tone"]
        if "template" in data:
            cover_letter.template = data["template"]

        cover_letter.version += 1

        db.commit()
        db.refresh(cover_letter)
        return cover_letter
