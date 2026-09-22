"""Resilient Dense Vector Index Expander for Indian Standards.

Incrementally indexes standards from standards_master.db using BGE-M3 embeddings,
checkpointing progress and merging vectors into dense_index.faiss without re-indexing
previously embedded standards.

Usage:
  # Index priority procurement standards (QCO, CPWD, GeM, Civil/Electrical core):
  python expand_dense_index.py --priority-only --limit 1000

  # Index next N un-indexed standards:
  python expand_dense_index.py --limit 500

  # Full incremental run:
  python expand_dense_index.py
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import faiss
import numpy as np

from src.retrieval.bge_multilingual_embedder import encode_texts

DATA_DIR = BASE_DIR / "data"
INDEX_DIR = DATA_DIR / "index"
DB_PATH = DATA_DIR / "standards_master.db"


def load_existing_index(index_dir: Path) -> tuple[faiss.Index, list[str], list[str]]:
    """Loads existing FAISS index and metadata."""
    faiss_path = index_dir / "dense_index.faiss"
    meta_path = index_dir / "dense_metadata.json"

    if not faiss_path.exists() or not meta_path.exists():
        raise FileNotFoundError(f"FAISS index or metadata not found at {index_dir}")

    index = faiss.read_index(str(faiss_path))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    if isinstance(meta, dict):
        is_codes = meta.get("is_codes", [])
        titles = meta.get("titles", [])
    else:
        is_codes = [m.get("is_code", "") for m in meta]
        titles = [m.get("title", "") for m in meta]

    return index, is_codes, titles


def get_unindexed_priority_standards(
    db_path: Path, existing_codes: set[str], limit: int | None = None
) -> list[dict[str, str]]:
    """Selects high-priority unindexed standards (QCO, Schedule items, active Civil/Electrical)."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Priority 1: Mandatory QCO standards
    cur.execute("SELECT DISTINCT is_code FROM qco_mandatory_rules")
    qco_codes = {r["is_code"] for r in cur.fetchall()}

    # Priority 2: Government schedule standards (CPWD / GeM)
    cur.execute("SELECT DISTINCT is_code FROM government_schedule_items WHERE is_code IS NOT NULL")
    sched_codes = {r["is_code"] for r in cur.fetchall()}

    # Query all active standards with title and scope
    cur.execute(
        """
        SELECT is_code, title, scope, division, status
        FROM standards_registry
        WHERE status = 'ACTIVE'
        ORDER BY 
            CASE 
                WHEN is_code IN ({qco_placeholders}) THEN 1
                WHEN is_code IN ({sched_placeholders}) THEN 2
                WHEN division LIKE '%Civil%' OR division LIKE '%CED%' THEN 3
                WHEN division LIKE '%Electrotechnical%' OR division LIKE '%ETD%' THEN 4
                WHEN division LIKE '%Mechanical%' OR division LIKE '%MED%' THEN 5
                ELSE 6
            END,
            is_code ASC
        """.format(
            qco_placeholders=",".join(f"'{c}'" for c in qco_codes) if qco_codes else "''",
            sched_placeholders=",".join(f"'{c}'" for c in sched_codes) if sched_codes else "''",
        )
    )

    unindexed = []
    for row in cur.fetchall():
        code = row["is_code"]
        if code in existing_codes:
            continue
        unindexed.append({
            "is_code": code,
            "title": row["title"] or "",
            "scope": row["scope"] or "",
            "division": row["division"] or "",
        })
        if limit and len(unindexed) >= limit:
            break

    conn.close()
    return unindexed


def main():
    parser = argparse.ArgumentParser(description="Expand FAISS dense index for Indian Standards.")
    parser.add_argument("--limit", type=int, default=200, help="Maximum number of standards to index in this run.")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for BGE-M3 embedding.")
    parser.add_argument("--priority-only", action="store_true", help="Index priority standards only (QCO, schedules).")
    args = parser.parse_args()

    print("=" * 70)
    print("  FAISS DENSE VECTOR INDEX EXPANDER")
    print("=" * 70)

    print(f"\n[1/4] Loading existing FAISS index from {INDEX_DIR} ...")
    index, is_codes, titles = load_existing_index(INDEX_DIR)
    initial_count = index.ntotal
    existing_set = set(is_codes)
    print(f"      Current index contains {initial_count} vectors.")

    print(f"\n[2/4] Querying unindexed standards from SQLite (Target limit: {args.limit}) ...")
    candidates = get_unindexed_priority_standards(DB_PATH, existing_set, limit=args.limit)
    if not candidates:
        print("      No unindexed candidates found. All matching standards already vectorized!")
        return

    print(f"      Found {len(candidates)} standards ready for vector embedding.")
    sample = candidates[0]
    print(f"      Sample candidate: {sample['is_code']} - {sample['title'][:55]}")

    print(f"\n[3/4] Generating BGE-M3 1024-d embeddings (Batch size: {args.batch_size}) ...")
    texts_to_encode = []
    new_codes = []
    new_titles = []

    for s in candidates:
        code = s["is_code"]
        title = s["title"]
        scope = (s["scope"] or "")[:500]
        text = f"Indian Standard {code}: {title}. Scope: {scope}"
        texts_to_encode.append(text)
        new_codes.append(code)
        new_titles.append(title)

    t0 = time.perf_counter()
    new_embeddings = encode_texts(texts_to_encode, batch_size=args.batch_size, show_progress_bar=True)
    elapsed = time.perf_counter() - t0
    print(f"      Encoded {len(new_embeddings)} vectors in {elapsed:.2f}s ({elapsed/len(new_embeddings):.2f}s/vector).")

    print(f"\n[4/4] Merging {len(new_embeddings)} new vectors into FAISS and saving ...")
    index.add(new_embeddings)
    is_codes.extend(new_codes)
    titles.extend(new_titles)

    # Save updated index
    faiss.write_index(index, str(INDEX_DIR / "dense_index.faiss"))
    meta = {"is_codes": is_codes, "titles": titles}
    (INDEX_DIR / "dense_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    final_count = index.ntotal
    print(f"      SUCCESS: Index expanded from {initial_count} to {final_count} vectors (+{len(new_codes)}).")
    print(f"      Index saved to: {INDEX_DIR / 'dense_index.faiss'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
