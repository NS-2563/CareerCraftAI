from typing import List, Optional
from sqlalchemy.orm import Session

from app.career.models import CareerReport


def save_report(
    db: Session,
    user_id: int,
    report: dict,
    source: str,
) -> CareerReport:
    """
    Save a generated career report.
    """

    record = CareerReport(
        user_id=user_id,
        career_goal=report.get(
            "career_goal",
            ""
        ),
        readiness_score=report.get(
            "readiness_score",
            0
        ),
        best_match=report.get(
            "best_match",
            ""
        ),
        source=source,
        report_json=report,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def get_history(
    db: Session,
    user_id: int,
) -> List[CareerReport]:
    """
    Get all career reports
    for a user.
    """

    return (
        db.query(CareerReport)
        .filter(
            CareerReport.user_id == user_id
        )
        .order_by(
            CareerReport.created_at.desc()
        )
        .all()
    )


def get_report(
    db: Session,
    report_id: int,
    user_id: int,
) -> Optional[CareerReport]:
    """
    Get one report.
    """

    return (
        db.query(CareerReport)
        .filter(
            CareerReport.id == report_id,
            CareerReport.user_id == user_id,
        )
        .first()
    )


def delete_report(
    db: Session,
    report_id: int,
    user_id: int,
) -> bool:
    """
    Delete one report.
    """

    report = get_report(
        db,
        report_id,
        user_id,
    )

    if not report:
        return False

    db.delete(report)
    db.commit()

    return True


def clear_history(
    db: Session,
    user_id: int,
) -> int:
    """
    Delete all reports
    belonging to a user.
    """

    deleted = (
    db.query(CareerReport)
    .filter(CareerReport.user_id == user_id)
    .delete(synchronize_session=False)
)

    db.commit()

    return deleted