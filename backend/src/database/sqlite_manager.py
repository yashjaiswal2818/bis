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


def extract_base_code(code: str) -> str:
    """Extracts base standard identifier without year or revision, lowercased and stripped of spaces.
    e.g. 'IS 456: 2000' -> 'is456'
         'IS 1489 (Part 1): 1991' -> 'is1489(part1)'
         'IS 10500' -> 'is10500'
    """
    cleaned = re.sub(r":\s*\d{4}.*$", "", str(code))
    return re.sub(r"\s+", "", cleaned).lower()


def validate_supersession(source_is_code: str, superseded_by: str | None, is_cross_code_allowed: bool = False) -> str | None:
    """Rejects any superseded_by value whose base code differs from the source, to prevent prefix-matching bugs."""
    if not superseded_by:
        return None
    source_base = extract_base_code(source_is_code)
    target_base = extract_base_code(superseded_by)
    if source_base != target_base and not is_cross_code_allowed:
        print(f"[Guard] Rejected invalid supersession: {source_is_code} -> {superseded_by}")
        return None
    return superseded_by


KNOWN_TEST_CODES = {"is4031", "is2386", "is516", "is1608", "is3025", "is12235", "is1966", "is3495", "is1727", "is1367"}
KNOWN_INSTALLATION_CODES = {"is7634", "is456", "is13920", "is1893", "is4021", "is2212", "is2250", "is1478", "is1742"}
KNOWN_SAFETY_CODES = {"is14489", "is1642", "is2925", "is15683", "is2171", "is3521", "is3844"}
KNOWN_TERMINOLOGY_CODES = {"is4845", "is2248", "is195", "is282", "is1800"}


def classify_relation(source_code: str, target_code: str, target_title: str) -> tuple[str, str]:
    """Classifies a cross-reference relationship into the 6-way BIS taxonomy based on code and title."""
    title_lower = target_title.lower() if target_title else ""
    code_base = extract_base_code(target_code)

    if code_base in KNOWN_TEST_CODES or any(k in title_lower for k in ["method of test", "testing", "sampling", "determination", "analysis", "test"]):
        return "NORM_TEST", "Normative Test & Sampling Method"
    elif code_base in KNOWN_INSTALLATION_CODES or any(k in title_lower for k in ["code of practice", "laying", "installation", "construction", "workmanship", "application", "detailing"]):
        return "INSTALLATION", "Installation & Workmanship Code"
    elif code_base in KNOWN_SAFETY_CODES or any(k in title_lower for k in ["safety", "fire", "protection", "health", "hazard", "prevention", "helmet", "extinguisher"]):
        return "SAFETY", "Safety & Environmental Standard"
    elif code_base in KNOWN_TERMINOLOGY_CODES or any(k in title_lower for k in ["glossary", "terminology", "definitions", "symbols"]):
        return "TERMINOLOGY", "Terminology & Definitions Standard"
    elif any(k in title_lower for k in ["admixture", "aggregate", "lime", "fly ash", "slag", "water", "bar", "steel", "cement"]):
        return "RAW_MATERIAL", "Allied Material / Component Specification"
    else:
        return "RELATED_PRODUCT", "Allied Co-Dependent Product Standard"


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
                base_code = extract_base_code(is_code)
                title = r.get("title", "").strip()
                revision = r.get("revision")
                scope = r.get("scope", "")
                full_text = r.get("full_text", "")
                
                # Check lifecycle metadata
                status = r.get("status", "ACTIVE")
                superseded_by = r.get("superseded_by")
                reaffirm_year = r.get("reaffirmation_year")
                amendments = r.get("amendments_count", 0)

                # Sample known revisions for building materials
                import re
                if "1989" in is_code and re.search(r'\b269(?=[:\s(]|$)', is_code):
                    status = "SUPERSEDED"
                    superseded_by = "IS 269: 2015"
                    reaffirm_year = 2021
                    amendments = 4

                superseded_by = validate_supersession(is_code, superseded_by)
                if status == "SUPERSEDED" and superseded_by is None:
                    status = "ACTIVE"

                standards_rows.append((
                    is_code,
                    is_code_norm,
                    base_code,
                    title,
                    revision,
                    scope,
                    full_text,
                    r.get("division", "Civil Engineering (CED)"),
                    status,
                    superseded_by,
                    reaffirm_year,
                    amendments,
                ))

            conn.executemany(
                """
                INSERT OR REPLACE INTO standards_registry 
                (is_code, is_code_norm, base_code, title, revision, scope, full_text, division, status, superseded_by, reaffirmation_year, amendments_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                base = extract_base_code(code)
                stub_standards.append((
                    code,
                    norm,
                    base,
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
                (is_code, is_code_norm, base_code, title, revision, scope, full_text, division, status, superseded_by, reaffirmation_year, amendments_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        extract_base_code(source_code),
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
                    (is_code, is_code_norm, base_code, title, revision, scope, full_text, division, status, superseded_by, reaffirmation_year, amendments_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    """Retrieves full standard record by canonical IS code, normalized code, or base code.
    If multiple versions match base_code (e.g. IS 269:1989 and IS 269:2015), prefers ACTIVE over SUPERSEDED.
    """
    code_norm = normalize_is_code(is_code)
    base_code = extract_base_code(is_code)
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM standards_registry WHERE is_code = ? OR is_code_norm = ?",
            (is_code, code_norm),
        ).fetchone()

        if not row:
            row = conn.execute(
                """
                SELECT * FROM standards_registry 
                WHERE base_code = ? 
                ORDER BY CASE WHEN status = 'ACTIVE' THEN 0 ELSE 1 END, is_code DESC
                LIMIT 1
                """,
                (base_code,),
            ).fetchone()

        if not row:
            return None
        res = dict(row)
        # Fetch QCO rules (match exact code or base standard)
        base = res.get("base_code") or extract_base_code(res["is_code"])
        all_qco = conn.execute("SELECT * FROM qco_compliance_rules").fetchall()
        matching_qco = []
        seen_orders = set()
        for q in all_qco:
            q_dict = dict(q)
            q_base = extract_base_code(q_dict["is_code"])
            if q_dict["is_code"] == res["is_code"] or q_base == base:
                order_key = (q_base, q_dict["order_name"])
                if order_key not in seen_orders:
                    seen_orders.add(order_key)
                    matching_qco.append(q_dict)
        res["qco_rules"] = matching_qco

        # Fetch Allied Standards (match bidirectional: exact code or base standard as source OR target)
        allied_rows = conn.execute(
            """
            SELECT DISTINCT 
                CASE 
                    WHEN a.source_is_code = ? OR src.base_code = ? THEN a.target_is_code 
                    ELSE a.source_is_code 
                END AS target_is_code,
                a.relation_type,
                a.relation_label,
                a.is_normative,
                COALESCE(
                    CASE 
                        WHEN a.source_is_code = ? OR src.base_code = ? THEN s.title 
                        ELSE src.title 
                    END, 
                    ''
                ) AS title
            FROM allied_standards_edges a
            LEFT JOIN standards_registry src ON a.source_is_code = src.is_code
            LEFT JOIN standards_registry s ON a.target_is_code = s.is_code
            WHERE a.source_is_code = ? OR src.base_code = ? OR a.target_is_code = ? OR s.base_code = ?
            """,
            (res["is_code"], base, res["is_code"], base, res["is_code"], base, res["is_code"], base),
        ).fetchall()

        seen_allied = set()
        deduped_allied = []
        for a in allied_rows:
            a_dict = dict(a)
            t_code = a_dict.get("target_is_code")
            if t_code and t_code != res["is_code"] and t_code not in seen_allied:
                seen_allied.add(t_code)
                deduped_allied.append(a_dict)
        res["allied_standards"] = deduped_allied
        return res


def get_all_standards_for_indexing(db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    """Retrieves all standards for generating dense and sparse embeddings."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT is_code, is_code_norm, title, revision, scope, full_text FROM standards_registry"
        ).fetchall()
        return [dict(r) for r in rows]
