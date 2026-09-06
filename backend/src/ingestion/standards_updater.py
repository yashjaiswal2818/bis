"""Incremental Standards Updater for Indian Standards.

Enables administrators to ingest newly published or revised Indian Standards
without re-training models or re-indexing the entire corpus from scratch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.database.sqlite_manager import (
    DB_PATH,
    get_all_standards_for_indexing,
    get_connection,
    normalize_is_code,
)
from src.retrieval.bge_multilingual_embedder import encode_texts
from src.retrieval.bm25_lexical_indexer import build_bm25_index
from src.retrieval.faiss_vector_indexer import FAISSDenseIndex


def update_standards(update_json_path: Path):
    """Ingests a JSON array of new or updated Indian Standards."""
    if not update_json_path.exists():
        print(f"[Error] Update file not found: {update_json_path}", file=sys.stderr)
        return

    records = json.loads(update_json_path.read_text(encoding="utf-8"))
    print(f"[Updater] Ingesting {len(records)} new/updated standards ...")

    data_dir = BASE_DIR / "data"
    index_dir = data_dir / "index"
    whitelist_path = data_dir / "is_code_whitelist.json"

    # 1. Update SQLite
    with get_connection(DB_PATH) as conn:
        for r in records:
            code = r["is_code"]
            norm = normalize_is_code(code)
            title = r.get("title", "")
            revision = r.get("revision", "Latest Published Version")
            scope = r.get("scope", "")
            full_text = r.get("full_text", "")
            division = r.get("division", "General Engineering")
            status = r.get("status", "ACTIVE")
            superseded_by = r.get("superseded_by")
            reaffirm = r.get("reaffirmation_year")
            amendments = r.get("amendments_count", 0)

            conn.execute(
                """
                INSERT OR REPLACE INTO standards_registry
                (is_code, is_code_norm, title, revision, scope, full_text, division, status, superseded_by, reaffirmation_year, amendments_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (code, norm, title, revision, scope, full_text, division, status, superseded_by, reaffirm, amendments),
            )
        conn.commit()
    print("[Updater] SQLite database updated.")

    # 2. Append to FAISS Dense Index
    dense_index = FAISSDenseIndex.load(index_dir)
    new_codes = []
    new_titles = []
    texts_to_encode = []

    for r in records:
        code = r["is_code"]
        title = r.get("title", "")
        scope = r.get("scope", "")
        new_codes.append(code)
        new_titles.append(title)
        texts_to_encode.append(f"Indian Standard {code}: {title}. Scope: {scope}")

    print("[Updater] Computing dense embeddings for new standards ...")
    new_embeddings = encode_texts(texts_to_encode, batch_size=16)
    dense_index.index.add(new_embeddings)
    dense_index.is_codes.extend(new_codes)
    dense_index.titles.extend(new_titles)
    dense_index.save(index_dir)
    print(f"[Updater] FAISS index successfully updated with {len(new_codes)} new standards.")

    # 3. Refresh BM25 Index
    print("[Updater] Refreshing BM25 sparse index ...")
    all_standards = get_all_standards_for_indexing(DB_PATH)
    build_bm25_index(all_standards, output_path=index_dir / "bm25_index.pkl")
    print("[Updater] BM25 index refreshed.")

    # 4. Update Whitelist
    whitelist_raw: dict[str, list[str]] = {"canonical": [], "normalized": []}
    if whitelist_path.exists():
        try:
            loaded = json.loads(whitelist_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                whitelist_raw = loaded
            elif isinstance(loaded, list):
                whitelist_raw = {"canonical": loaded, "normalized": [normalize_is_code(c) for c in loaded]}
        except Exception:
            pass
    canonical_set = set(whitelist_raw.get("canonical", []))
    norm_set = set(whitelist_raw.get("normalized", []))
    for r in records:
        canonical_set.add(r["is_code"])
        norm_set.add(normalize_is_code(r["is_code"]))
    whitelist_raw["canonical"] = sorted(list(canonical_set))
    whitelist_raw["normalized"] = sorted(list(norm_set))
    whitelist_path.write_text(json.dumps(whitelist_raw, indent=2), encoding="utf-8")
    print("[Updater] Whitelist synchronized.")
    print("[Updater] All updates complete!")


def main():
    parser = argparse.ArgumentParser(description="Incremental Indian Standards Ingestion Updater")
    parser.add_argument("--file", "-f", type=str, required=True, help="Path to JSON file containing new standards")
    args = parser.parse_args()
    update_standards(Path(args.file))


if __name__ == "__main__":
    main()
