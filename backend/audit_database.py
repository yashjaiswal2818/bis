"""Comprehensive Audit of Master Indian Standards Database."""
import sqlite3
import re
from pathlib import Path

DB_PATH = Path("backend/data/standards_master.db")

def audit():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    total = c.execute("SELECT count(*) FROM standards_registry").fetchone()[0]
    unique_is_code = c.execute("SELECT count(DISTINCT is_code) FROM standards_registry").fetchone()[0]
    unique_norm = c.execute("SELECT count(DISTINCT is_code_norm) FROM standards_registry").fetchone()[0]
    unique_base = c.execute("SELECT count(DISTINCT base_code) FROM standards_registry").fetchone()[0]

    print("=" * 70)
    print("  DATABASE INTEGRITY AUDIT")
    print("=" * 70)
    print(f"Total Rows in standards_registry : {total:,}")
    print(f"Unique is_code                   : {unique_is_code:,}")
    print(f"Unique is_code_norm              : {unique_norm:,}")
    print(f"Unique base_code (Core standards): {unique_base:,}")

    # Check multiple editions/versions of the same standard
    print("\n--- SAMPLE MULTI-EDITION / MULTI-PART STANDARDS ---")
    c.execute("""
        SELECT base_code, count(*) as cnt 
        FROM standards_registry 
        GROUP BY base_code 
        HAVING cnt > 1 
        ORDER BY cnt DESC 
        LIMIT 10
    """)
    multi_editions = c.fetchall()
    for base, cnt in multi_editions:
        print(f"\nBase: {base} ({cnt} versions/parts):")
        c.execute("SELECT is_code, title, revision, status FROM standards_registry WHERE base_code = ?", (base,))
        for r in c.fetchall():
            print(f"   -> {r[0]:<28} | {r[1][:40]} | {r[2]} | {r[3]}")

    # Inspect specific benchmark standards
    print("\n--- BENCHMARK CRITICAL STANDARDS CHECK ---")
    crit_codes = ["is269", "is8112", "is12269", "is456", "is1417", "is16046(part2)", "is10500", "is1786", "is6909", "is8042"]
    for code in crit_codes:
        c.execute("SELECT is_code, title, division, status FROM standards_registry WHERE base_code = ?", (code,))
        rows = c.fetchall()
        print(f"Base '{code}': {len(rows)} matching rows:")
        for r in rows:
            print(f"   {r[0]:<28} | {r[1][:45]} | {r[2]}")

    # Check for empty or corrupt titles/scopes
    empty_titles = c.execute("SELECT count(*) FROM standards_registry WHERE title IS NULL OR length(trim(title)) = 0").fetchone()[0]
    empty_scopes = c.execute("SELECT count(*) FROM standards_registry WHERE scope IS NULL OR length(trim(scope)) = 0").fetchone()[0]
    print(f"\nEmpty/blank titles: {empty_titles}")
    print(f"Empty/blank scopes: {empty_scopes}")

    # Check QCO integrity
    qco_total = c.execute("SELECT count(*) FROM qco_compliance_rules").fetchone()[0]
    qco_matched = c.execute("""
        SELECT count(*) FROM qco_compliance_rules q 
        JOIN standards_registry s ON q.is_code = s.is_code
    """).fetchone()[0]
    print(f"\nQCO Rules: {qco_total} rules, {qco_matched} directly linked to standards_registry")

    # Check Allied edges integrity
    allied_total = c.execute("SELECT count(*) FROM allied_standards_edges").fetchone()[0]
    allied_matched_src = c.execute("""
        SELECT count(*) FROM allied_standards_edges a 
        JOIN standards_registry s ON a.source_is_code = s.is_code
    """).fetchone()[0]
    print(f"Allied Edges: {allied_total} edges, {allied_matched_src} source nodes valid in standards_registry")

if __name__ == "__main__":
    audit()
