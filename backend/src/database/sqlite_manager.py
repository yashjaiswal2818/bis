"""SQLite Manager for the BIS Recommendation Engine.

Handles schema initialization, database migrations, seed data loading,
and optimized query interfaces for standards, QCO compliance, and allied graphs.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "standards_master.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory enabled for dictionary-like access."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database(db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH) -> None:
    """Executes schema.sql to create all tables and indices."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with get_connection(db_path) as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()


def normalize_is_code(code: str) -> str:
    """Canonical normalization matching eval script (strips spaces, lowercases)."""
    return re.sub(r"\s+", "", code).lower()


def classify_relation(source_code: str, target_code: str, target_title: str) -> tuple[str, str]:
    """Classifies a cross-reference relationship based on title and keywords."""
    title_lower = target_title.lower() if target_title else ""
    if any(k in title_lower for k in ["method of test", "testing", "sampling", "determination", "analysis", "test"]):
        return "NORM_TEST", "Normative Test & Sampling Method"
    elif any(k in title_lower for k in ["code of practice", "laying", "installation", "construction", "workmanship", "application"]):
        return "INSTALLATION", "Installation & Workmanship Code"
    elif any(k in title_lower for k in ["safety", "fire", "protection", "health", "hazard", "prevention"]):
        return "SAFETY", "Safety & Environmental Standard"
    elif any(k in title_lower for k in ["glossary", "terminology", "definitions", "symbols"]):
        return "TERMINOLOGY", "Terminology & Definitions Standard"
    else:
        return "RAW_MATERIAL", "Allied Material / Component Specification"


def seed_database_from_files(
    standards_json: Path,
    qco_json: Path,
    xrefs_json: Path,
    db_path: Path = DB_PATH,
) -> dict[str, int]:
    """Populates SQLite database with standards, QCO rules, and allied graph edges."""
    initialize_database(db_path)
    counts = {"standards": 0, "qco_rules": 0, "allied_edges": 0}

    with get_connection(db_path) as conn:
        # 1. Ingest Master Standards
        if standards_json.exists():
            records = json.loads(standards_json.read_text(encoding="utf-8"))
            standards_rows = []
            for r in records:
                is_code = r.get("is_code", "").strip()
                if not is_code:
                    continue
                is_code_norm = normalize_is_code(is_code)
                title = r.get("title", "").strip()
                revision = r.get("revision")
                scope = r.get("scope", "")
                full_text = r.get("full_text", "")
                
                # Check lifecycle metadata
                status = "ACTIVE"
                superseded_by = None
                reaffirm_year = None
                amendments = 0

                # Sample known revisions for building materials
                if "1989" in is_code and "269" in is_code:
                    status = "SUPERSEDED"
                    superseded_by = "IS 269: 2015"
                    reaffirm_year = 2021
                    amendments = 4

                standards_rows.append((
                    is_code,
                    is_code_norm,
                    title,
                    revision,
                    scope,
                    full_text,
                    "Civil Engineering (CED)",
                    status,
                    superseded_by,
                    reaffirm_year,
                    amendments,
                ))

            conn.executemany(
                """
                INSERT OR REPLACE INTO standards_registry 
                (is_code, is_code_norm, title, revision, scope, full_text, division, status, superseded_by, reaffirmation_year, amendments_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                standards_rows,
            )
            counts["standards"] = len(standards_rows)

        # 2. Ingest Mandatory QCO Rules (auto-register missing standards)
        if qco_json.exists():
            qco_records = json.loads(qco_json.read_text(encoding="utf-8"))
            qco_rows = []
            stub_standards = []
            for q in qco_records:
                code = q["is_code"]
                norm = normalize_is_code(code)
                stub_standards.append((
                    code,
                    norm,
                    q["product_category"],
                    "Latest Published Version",
                    f"Specification covering {q['product_category']}",
                    f"Full text for {code}",
                    q["issuing_ministry"],
                    "ACTIVE",
                    None,
                    None,
                    0,
                ))
                qco_rows.append((
                    code,
                    q["product_category"],
                    q["scheme_type"],
                    1 if q.get("is_mandatory", True) else 0,
                    q["issuing_ministry"],
                    q["order_name"],
                    q.get("effective_date"),
                    q["compliance_warning"],
                ))

            # Insert stubs if not already present
            conn.executemany(
                """
                INSERT OR IGNORE INTO standards_registry
                (is_code, is_code_norm, title, revision, scope, full_text, division, status, superseded_by, reaffirmation_year, amendments_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                stub_standards,
            )

            conn.executemany(
                """
                INSERT OR REPLACE INTO qco_compliance_rules
                (is_code, product_category, scheme_type, is_mandatory, issuing_ministry, order_name, effective_date, compliance_warning)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                qco_rows,
            )
            counts["qco_rules"] = len(qco_rows)

        # 3. Ingest and Classify Allied Standards Knowledge Graph
        if xrefs_json.exists():
            raw_xrefs = json.loads(xrefs_json.read_text(encoding="utf-8"))
            # Build title lookup for target standards
            cursor = conn.cursor()
            cursor.execute("SELECT is_code, title FROM standards_registry")
            title_map = {row["is_code"]: row["title"] for row in cursor.fetchall()}

            # Ensure all source codes exist in standards_registry
            source_stubs = []
            for source_code in raw_xrefs.keys():
                if source_code not in title_map:
                    source_stubs.append((
                        source_code,
                        normalize_is_code(source_code),
                        "Indian Standard Specification",
                        "Latest Edition",
                        "",
                        "",
                        "Civil Engineering (CED)",
                        "ACTIVE",
                        None,
                        None,
                        0,
                    ))
            if source_stubs:
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO standards_registry
                    (is_code, is_code_norm, title, revision, scope, full_text, division, status, superseded_by, reaffirmation_year, amendments_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    source_stubs,
                )

            edges_rows = []
            for source_code, target_list in raw_xrefs.items():
                for target_code in target_list:
                    target_title = title_map.get(target_code, "")
                    rel_type, rel_label = classify_relation(source_code, target_code, target_title)
                    edges_rows.append((
                        source_code,
                        target_code,
                        rel_type,
                        rel_label,
                        1 if rel_type in ["NORM_TEST", "SAFETY"] else 0,
                    ))

            conn.executemany(
                """
                INSERT INTO allied_standards_edges
                (source_is_code, target_is_code, relation_type, relation_label, is_normative)
                VALUES (?, ?, ?, ?, ?)
                """,
                edges_rows,
            )
            counts["allied_edges"] = len(edges_rows)

        conn.commit()
    return counts


# --- Query Helpers ---

def get_standard_details(is_code: str, db_path: Path = DB_PATH) -> dict[str, Any] | None:
    """Retrieves full standard record by canonical IS code."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM standards_registry WHERE is_code = ? OR is_code_norm = ?",
            (is_code, normalize_is_code(is_code)),
        ).fetchone()
        if not row:
            return None
        res = dict(row)
        # Fetch QCO rules
        qco_rows = conn.execute(
            "SELECT * FROM qco_compliance_rules WHERE is_code = ?",
            (res["is_code"],),
        ).fetchall()
        res["qco_rules"] = [dict(q) for q in qco_rows]

        # Fetch Allied Standards
        allied_rows = conn.execute(
            """
            SELECT a.target_is_code, a.relation_type, a.relation_label, a.is_normative, s.title
            FROM allied_standards_edges a
            LEFT JOIN standards_registry s ON a.target_is_code = s.is_code
            WHERE a.source_is_code = ?
            """,
            (res["is_code"],),
        ).fetchall()
        res["allied_standards"] = [dict(a) for a in allied_rows]
        return res


def get_all_standards_for_indexing(db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    """Retrieves all standards for generating dense and sparse embeddings."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT is_code, is_code_norm, title, revision, scope, full_text FROM standards_registry"
        ).fetchall()
        return [dict(r) for r in rows]
