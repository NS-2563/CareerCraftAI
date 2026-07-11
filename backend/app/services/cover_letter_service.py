from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List
import json

from app.models.cover_letter import CoverLetter
from app.schemas.cover_letter import CoverLetterCreate, CoverLetterUpdate
from app.utils.exceptions import NotFoundException


def _to_json(data) -> str:
    """Convert dict/list to JSON string."""
    if data is None:
        return "[]"
    try:
        return json.dumps(data)
    except:
        return "[]"


def _from_json(text: str) -> dict:
    """Convert JSON string to dict."""
    if text:
        try:
            return json.loads(text)
        except:
            pass
    return {}


def _create_version_snapshot(cover_letter: CoverLetter, note: str = None) -> dict:
    """Create a version snapshot of the cover letter."""
    return {
        "version": cover_letter.version,
        "timestamp": datetime.utcnow().isoformat(),
        "note": note,
        "data": {
            "title": cover_letter.title,
            "content": cover_letter.content,
            "job_title": cover_letter.job_title,
            "company_name": cover_letter.company_name,
            "job_description": cover_letter.job_description,
            "tone": cover_letter.tone,
            "template": cover_letter.template,
        },
    }


class CoverLetterService:
    """Service for cover letter CRUD operations."""

    @staticmethod
    def create(db: Session, user_id: int, cover_letter_data: CoverLetterCreate) -> CoverLetter:
        """Create a new cover letter."""
        cover_letter = CoverLetter(
            user_id=user_id,
            resume_id=cover_letter_data.resume_id,
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
        return cover_letter

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
    def get_all(db: Session, user_id: int, resume_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[CoverLetter]:
        """Get all cover letters for a user."""
        query = db.query(CoverLetter).filter(
            CoverLetter.user_id == user_id,
            CoverLetter.is_archived == False,
        )
        if resume_id:
            query = query.filter(CoverLetter.resume_id == resume_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, cover_letter_id: int, user_id: int, cover_letter_data: CoverLetterUpdate) -> CoverLetter:
        """Update an existing cover letter."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)

        # Create version snapshot before updating
        snapshot = _create_version_snapshot(cover_letter, "Before update")
        history = _from_json(cover_letter.version_history) if cover_letter.version_history else []
        history.append(snapshot)
        # Keep last 50 versions
        cover_letter.version_history = _to_json(history[-50:])

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

        # Increment version
        cover_letter.version += 1

        db.commit()
        db.refresh(cover_letter)
        return cover_letter

    @staticmethod
    def delete(db: Session, cover_letter_id: int, user_id: int) -> None:
        """Delete a cover letter."""
        cover_letter = CoverLetterService.get_by_id(db, cover_letter_id, user_id)
        db.delete(cover_letter)
        db.commit()

    @staticmethod
    def duplicate(db: Session, cover_letter_id: int, user_id: int, new_title: str) -> CoverLetter:
        """Duplicate a cover letter."""
        original = CoverLetterService.get_by_id(db, cover_letter_id, user_id)

        new_cover_letter = CoverLetter(
            user_id=user_id,
            resume_id=original.resume_id,
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
        return _from_json(cover_letter.version_history) if cover_letter.version_history else []

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
        history = _from_json(cover_letter.version_history) if cover_letter.version_history else []

        # Find the version snapshot
        target = None
        for v in history:
            if v.get("version") == version:
                target = v
                break

        if not target:
            raise NotFoundException(f"Version {version}", "not found")

        data = target.get("data", {})

        # Create snapshot before restoring
        snapshot = _create_version_snapshot(cover_letter, f"Before restore to v{version}")
        history.append(snapshot)
        cover_letter.version_history = _to_json(history[-50:])

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