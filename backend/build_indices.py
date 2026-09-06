"""Master Index Builder & Database Seeder.

1. Seeds SQLite standards_master.db with standards, QCO rules, and allied edges.
2. Builds BM25 sparse index (bm25_index.pkl).
3. Builds FAISS 1024-d dense vector index (dense_index.faiss).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.database.sqlite_manager import (
    get_all_standards_for_indexing,
    seed_database_from_files,
)
from src.retrieval.bm25_lexical_indexer import build_bm25_index
from src.retrieval.faiss_vector_indexer import build_faiss_index


def main():
    print("=" * 60)
    print("  BIS RECOMMENDATION ENGINE: SEEDING & INDEX BUILD")
    print("=" * 60)

    data_dir = BASE_DIR / "data"
    standards_json = data_dir / "parsed_standards.json"
    qco_json = data_dir / "qco_mandatory_catalog.json"
    xrefs_json = data_dir / "raw_xrefs.json"
    index_dir = data_dir / "index"
    db_path = data_dir / "standards_master.db"

    # 1. Seed SQLite
    print("\n[1/3] Seeding SQLite database (standards_master.db) ...")
    t0 = time.perf_counter()
    counts = seed_database_from_files(
        standards_json=standards_json,
        qco_json=qco_json,
        xrefs_json=xrefs_json,
        db_path=db_path,
    )
    print(f"      Seeded {counts['standards']} standards, {counts['qco_rules']} QCO rules, {counts['allied_edges']} allied edges in {time.perf_counter() - t0:.2f}s")

    # Fetch all records for indexing
    standards = get_all_standards_for_indexing(db_path)
    print(f"      Loaded {len(standards)} records from SQLite for indexing.")

    # 2. Build BM25 Index
    print("\n[2/3] Building BM25 lexical index (bm25_index.pkl) ...")
    t0 = time.perf_counter()
    bm25_path = index_dir / "bm25_index.pkl"
    build_bm25_index(standards, output_path=bm25_path)
    print(f"      BM25 index built and saved in {time.perf_counter() - t0:.2f}s")

    # 3. Build FAISS Dense Vector Index
    print("\n[3/3] Building FAISS dense index (dense_index.faiss via BGE-M3) ...")
    print("      (Note: First run will download BGE-M3 model weights (~2 GB) to cache)")
    t0 = time.perf_counter()
    build_faiss_index(standards, output_dir=index_dir, batch_size=16)
    print(f"      FAISS dense index built in {time.perf_counter() - t0:.2f}s")

    print("\n" + "=" * 60)
    print("  SUCCESS: All databases and indexes are ready for offline inference!")
    print("=" * 60)


if __name__ == "__main__":
    main()
