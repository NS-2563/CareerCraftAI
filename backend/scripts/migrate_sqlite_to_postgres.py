"""One-time migration utility: copy data from SQLite into PostgreSQL.

This is a purpose-built, one-time data migration. It does NOT change any model,
router, or business logic. It reads every table out of a SQLite database and
writes the rows into the matching tables of the PostgreSQL database, walking
tables in foreign-key dependency order so references are satisfied before they
are read back.

Features
--------
* Schema-driven: it imports all SQLAlchemy models so ``Base.metadata`` describes
  the full (PostgreSQL) target schema. Both source reads and destination writes
  use the *same* Table metadata, so JSON columns are de-serialized on read and
  re-serialized on write without double-encoding, and enum columns round-trip
  through the same processors (so their persisted values are preserved exactly).
* Column-intersection copy: only columns present in *both* the source table and
  the target table are copied, so minor schema drift between the databases
  cannot break the migration.
* FK-safe ordering: ``Base.metadata.sorted_tables`` yields parents before
  children. Foreign-key constraints stay ENABLED, so any ordering/relationship
  problem surfaces as a real insert error against the target.
* Datetime preservation: SQLite stores naive UTC datetimes. Values destined for
  ``timestamptz`` (``DateTime(timezone=True)``) columns are re-tagged as aware
  UTC so PostgreSQL does not interpret them in a different session timezone;
  values destined for plain ``timestamp`` columns are left naive. Wall-clock UTC
  values are preserved in both cases.
* Sequence reset: after copying explicit primary keys, each target serial
  sequence is repositioned past the highest copied id so future inserts do not
  collide.
* Idempotent re-runs: in ``--execute`` mode target tables are cleared (children
  first) before copying, so re-running replaces the existing target contents.

Usage
-----
    python scripts/migrate_sqlite_to_postgres.py            # dry-run report
    python scripts/migrate_sqlite_to_postgres.py --execute  # clear + copy

Both URLs can also be supplied via the ``SQLITE_SOURCE_URL`` and
``POSTGRES_DEST_URL`` environment variables (command-line flags win).
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import DateTime, create_engine, inspect, select, text
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("migrate")

# Import every model so Base.metadata describes the full target schema.
from app.database import Base  # noqa: E402
from app.models.user import User  # noqa: E402,F401
from app.models.resume import Resume  # noqa: E402,F401
from app.models.career_report import CareerReport  # noqa: E402,F401
from app.models.job_application import JobApplication  # noqa: E402,F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: E402,F401
from app.models.cover_letter import CoverLetter  # noqa: E402,F401
from app.models.jd_match_result import JDMatchResult  # noqa: E402,F401
from app.models.roadmap_task_status import RoadmapTaskStatus  # noqa: E402,F401
from app.models.insight_dismissal import InsightDismissal  # noqa: E402,F401
from app.communication.models import CommunicationMessage, CommunicationSuggestion  # noqa: E402,F401
from app.interview_prep.models import InterviewSession  # noqa: E402,F401
from app.activity.models import ActivityEvent  # noqa: E402,F401
from app.analytics.models import ScoreSnapshot  # noqa: E402,F401


class MigrationError(Exception):
    """Raised when the migration cannot proceed."""


def _build_engines(source_url: str, dest_url: str):
    if not source_url.startswith("sqlite"):
        raise MigrationError(f"Source URL must be a SQLite URL, got: {source_url}")
    if not dest_url.startswith(("postgresql", "postgres")):
        raise MigrationError(f"Destination URL must be a PostgreSQL URL, got: {dest_url}")
    source = create_engine(
        source_url, connect_args={"check_same_thread": False}, echo=False
    )
    dest = create_engine(dest_url, echo=False)
    return source, dest


def _column_names(engine, table_name: str) -> list:
    return [col["name"] for col in inspect(engine).get_columns(table_name)]


def _count(conn, table_name: str) -> int:
    return conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar() or 0


def _normalize_row(row: dict, table) -> dict:
    """Re-tag naive-UTC datetimes as aware UTC for timestamptz columns."""
    for col in table.columns:
        if not isinstance(col.type, DateTime) or not getattr(col.type, "timezone", False):
            continue
        value = row.get(col.name)
        if isinstance(value, datetime) and value.tzinfo is None:
            row[col.name] = value.replace(tzinfo=timezone.utc)
    return row


def _copy_table(source_conn, dest_session, table) -> int:
    """Copy rows from the source table into the destination table.

    Only columns present in both sides are copied. Returns rows inserted.
    Raises on any insert failure so the caller can mark the table FAIL.
    """
    src_columns = _column_names(source_conn.engine, table.name)
    common = [col for col in table.columns if col.name in src_columns]
    if not common:
        return 0
    sel = select(*[table.c[c.name] for c in common])
    rows = [dict(r) for r in source_conn.execute(sel).mappings().all()]
    if not rows:
        return 0
    data = [_normalize_row(r, table) for r in rows]
    dest_session.execute(table.insert().values(data))
    return len(data)


def _clear_tables(dest_conn, tables) -> None:
    """Delete rows from target tables, children first, so FK order is safe."""
    for table in reversed(tables):
        dest_conn.execute(text(f'DELETE FROM "{table.name}"'))


def _reset_sequences(dest_session, tables) -> int:
    """Reposition each serial sequence past the max copied id. Returns count."""
    resets = 0
    for table in tables:
        pk_cols = list(table.primary_key.columns)
        if len(pk_cols) != 1:
            continue
        pk = pk_cols[0].name
        seq_row = dest_session.execute(
            text("SELECT pg_get_serial_sequence(:t, :c)"),
            {"t": table.name, "c": pk},
        ).first()
        if not seq_row or not seq_row[0]:
            continue
        dest_session.execute(
            text(
                f'SELECT setval(pg_get_serial_sequence(:t, :c), '
                f'COALESCE(MAX("{pk}"), 1), true) FROM "{table.name}"'
            ),
            {"t": table.name, "c": pk},
        )
        resets += 1
    return resets


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate SQLite -> PostgreSQL data")
    parser.add_argument("--mode", choices=["dry-run", "execute"], default="dry-run",
                        help="dry-run (default, report only) or execute (clear + copy)")
    parser.add_argument("--source", default=os.environ.get(
        "SQLITE_SOURCE_URL", "sqlite:///./backup_careercraft.db"))
    parser.add_argument("--dest", default=os.environ.get("POSTGRES_DEST_URL", None))
    args = parser.parse_args()

    if args.dest is None:
        from app.config import settings
        args.dest = settings.DATABASE_URL

    execute = args.mode == "execute"
    source, dest = _build_engines(args.source, args.dest)
    tables = list(Base.metadata.sorted_tables)

    logger.info("Source : %s", args.source)
    logger.info("Dest   : %s", args.dest)
    logger.info("Mode   : %s", "EXECUTE" if execute else "DRY-RUN")
    logger.info("Tables : %d (FK dependency order)", len(tables))

    header = (f"{'Table':<28}{'SQLite':>9}{'Postgres(before)':>18}"
              f"{'Postgres(after)':>18}  Status")
    print("\n" + header)
    print("-" * len(header))

    if execute:
        with dest.connect() as conn:
            _clear_tables(conn, tables)
            conn.commit()
        logger.info("Cleared target tables (children first).")

    all_ok = True
    with Session(source) as src_session, Session(dest) as dest_session:
        for table in tables:
            src_count = _count(src_session.connection(), table.name)
            dest_before = _count(dest_session.connection(), table.name)

            if not execute:
                # Dry-run: report current source vs current target counts.
                status = "PASS" if src_count == dest_before else "MISMATCH"
                print(f"{table.name:<28}{src_count:>9}{dest_before:>18}{'-':>18}  {status}")
                continue

            try:
                copied = _copy_table(src_session.connection(), dest_session, table)
                dest_session.commit()
            except Exception as exc:  # noqa: BLE001
                dest_session.rollback()
                all_ok = False
                print(f"{table.name:<28}{src_count:>9}{dest_before:>18}{'ERR':>18}  FAIL  ({exc})")
                continue

            dest_after = _count(dest_session.connection(), table.name)
            ok = (copied == src_count) and (dest_after == src_count)
            if not ok:
                all_ok = False
            print(f"{table.name:<28}{src_count:>9}{dest_before:>18}{dest_after:>18}  "
                  f"{'PASS' if ok else 'FAIL'}")

    if execute:
        with Session(dest) as ds:
            n = _reset_sequences(ds, tables)
            ds.commit()
        print(f"\nReset {n} serial sequence(s) past max copied ids.")

    print("\n" + "-" * len(header))
    print(f"RESULT: {'PASS' if all_ok else 'FAIL — one or more tables did not migrate'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())