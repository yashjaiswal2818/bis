"""Allied Standards Classifier and Graph Traversal Module.

Extracts and categorizes connected standards from SQLite into
Normative Test Methods, Raw Materials, Safety, and Installation codes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.database.sqlite_manager import DB_PATH, get_connection


@dataclass
class CategorizedAlliedStandards:
    source_is_code: str
    normative_tests: list[dict[str, Any]] = field(default_factory=list)
    raw_materials: list[dict[str, Any]] = field(default_factory=list)
    safety_codes: list[dict[str, Any]] = field(default_factory=list)
    installation_codes: list[dict[str, Any]] = field(default_factory=list)
    terminology: list[dict[str, Any]] = field(default_factory=list)
    other_allied: list[dict[str, Any]] = field(default_factory=list)


class AlliedStandardsClassifier:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def get_classified_allied_standards(self, is_code: str) -> CategorizedAlliedStandards:
        """Retrieves and groups all allied standards for a core standard."""
        result = CategorizedAlliedStandards(source_is_code=is_code)

        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT a.target_is_code, a.relation_type, a.relation_label, a.is_normative, s.title
                FROM allied_standards_edges a
                LEFT JOIN standards_registry s ON a.target_is_code = s.is_code
                WHERE a.source_is_code = ?
                ORDER BY a.is_normative DESC, a.relation_type ASC
                """,
                (is_code,),
            ).fetchall()

            # allied_standards_edges holds 2,404 rows but only 628 distinct (source, target)
            # pairs, so the same code would otherwise be listed several times in a tender
            # clause. Dedupe on target at query time, keeping the first (highest-ranked) row.
            seen_targets: set[str] = set()
            for r in rows:
                target = str(r["target_is_code"])
                if target in seen_targets:
                    continue
                seen_targets.add(target)
                item: dict[str, Any] = {
                    "is_code": str(r["target_is_code"]),
                    "title": str(r["title"] or "Indian Standard Specification"),
                    "label": str(r["relation_label"] or ""),
                    "is_normative": bool(r["is_normative"]),
                }
                rel_type = r["relation_type"]
                if rel_type == "NORM_TEST":
                    result.normative_tests.append(item)
                elif rel_type == "RAW_MATERIAL":
                    result.raw_materials.append(item)
                elif rel_type == "SAFETY":
                    result.safety_codes.append(item)
                elif rel_type == "INSTALLATION":
                    result.installation_codes.append(item)
                elif rel_type == "TERMINOLOGY":
                    result.terminology.append(item)
                else:
                    result.other_allied.append(item)

        return result
