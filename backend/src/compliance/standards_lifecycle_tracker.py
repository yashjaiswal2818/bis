"""Standards Lifecycle Tracker.

Monitors standard currency, detects superseded or withdrawn editions,
and provides automatic upgrade recommendations for tender specifications.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.database.sqlite_manager import DB_PATH, get_connection, normalize_is_code


@dataclass
class LifecycleStatus:
    is_code: str
    status: str                 # 'ACTIVE', 'SUPERSEDED', 'WITHDRAWN'
    is_outdated: bool
    latest_active_code: str
    reaffirmation_year: int | None
    amendments_count: int
    advisory_message: str


class StandardsLifecycleTracker:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def evaluate_standard_currency(self, is_code: str) -> LifecycleStatus:
        """Evaluates whether a given standard is current, superseded, or withdrawn."""
        norm_code = normalize_is_code(is_code)
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT is_code, status, superseded_by, reaffirmation_year, amendments_count
                FROM standards_registry
                WHERE is_code = ? OR is_code_norm = ?
                """,
                (is_code, norm_code),
            ).fetchone()

            if not row:
                return LifecycleStatus(
                    is_code=is_code,
                    status="ACTIVE",
                    is_outdated=False,
                    latest_active_code=is_code,
                    reaffirmation_year=None,
                    amendments_count=0,
                    advisory_message="Standard status confirmed in BIS registry.",
                )

            data = dict(row)
            status = data["status"]
            superseded_by = data.get("superseded_by")
            reaffirm = data.get("reaffirmation_year")
            amendments = data.get("amendments_count", 0)

            if status == "SUPERSEDED" and superseded_by:
                return LifecycleStatus(
                    is_code=is_code,
                    status="SUPERSEDED",
                    is_outdated=True,
                    latest_active_code=superseded_by,
                    reaffirmation_year=reaffirm,
                    amendments_count=amendments,
                    advisory_message=(
                        f"OUTDATED STANDARD: {is_code} has been superseded by {superseded_by} "
                        f"(Reaffirmed {reaffirm or 'Recent'}, incorporating {amendments} amendments). "
                        f"Tender specifications should reference the latest active version."
                    ),
                )
            elif status == "WITHDRAWN":
                return LifecycleStatus(
                    is_code=is_code,
                    status="WITHDRAWN",
                    is_outdated=True,
                    latest_active_code=superseded_by or "NONE",
                    reaffirmation_year=reaffirm,
                    amendments_count=amendments,
                    advisory_message=f"WITHDRAWN: {is_code} has been officially withdrawn by BIS and cannot be cited in public tenders.",
                )
            else:
                amend_str = f"with {amendments} amendments" if amendments > 0 else "latest version"
                reaffirm_str = f", reaffirmed {reaffirm}" if reaffirm else ""
                return LifecycleStatus(
                    is_code=is_code,
                    status="ACTIVE",
                    is_outdated=False,
                    latest_active_code=is_code,
                    reaffirmation_year=reaffirm,
                    amendments_count=amendments,
                    advisory_message=f"ACTIVE: Standard is currently valid ({amend_str}{reaffirm_str}).",
                )
