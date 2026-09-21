"""Full BGE-M3 Dense Index Builder for Indian Standards.

Encodes all 33,564 standards from standards_master.db using BAAI/bge-m3 (1024 dimensions).
Features:
- Incremental checkpointing every 250 standards (resumable across reboots / interruptions).
- Low system impact: Throttles PyTorch CPU threads to 3 to keep system responsive.
- Real-time telemetry: Writes progress to backend/data/index/indexing_status.json.
- Atomic completion: Stages files in a checkpoint folder and swaps to production only when 100% complete.
"""
from __future__ import annotations

import gc
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# Enforce offline execution from local cache and prevent thread contention
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import faiss
import numpy as np
import torch

torch.set_num_threads(min(3, max(1, (os.cpu_count() or 4) - 1)))

from src.retrieval.bge_multilingual_embedder import get_embedder

DB_PATH = BACKEND_DIR / "data" / "standards_master.db"
OUTPUT_DIR = BACKEND_DIR / "data" / "index"
STAGING_DIR = OUTPUT_DIR / "staging_bge_m3"
STATUS_FILE = OUTPUT_DIR / "indexing_status.json"

CHECKPOINT_INTERVAL = 250
BATCH_SIZE = 16


def update_status(completed: int, total: int, start_time: float, status: str = "RUNNING"):
    elapsed = time.time() - start_time
    rate = completed / elapsed if elapsed > 0 and completed > 0 else 0.0
    remaining_sec = (total - completed) / rate if rate > 0 else 0.0

    payload = {
        "completed": completed,
        "total": total,
        "percentage": round((completed / total) * 100, 2) if total > 0 else 0.0,
        "elapsed_minutes": round(elapsed / 60, 1),
        "eta_hours": round(remaining_sec / 3600, 2),
        "standards_per_second": round(rate, 2),
        "status": status,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    STATUS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_indexing(embedder_model=None, live_orchestrator=None):
    print("=" * 80)
    print("STARTING FULL BGE-M3 DENSE INDEX BUILD (1024 DIMENSIONS)")
    print(f"Target DB: {DB_PATH}")
    print(f"Staging Directory: {STAGING_DIR}")
    print("=" * 80)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    chk_meta = STAGING_DIR / "checkpoint_meta.json"
    chk_emb = STAGING_DIR / "checkpoint_embeddings.npy"

    # 1. Fetch all standards from SQLite
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT is_code, title, scope FROM standards_registry ORDER BY is_code ASC")
    rows = cursor.fetchall()
    total_standards = len(rows)
    print(f">> Loaded {total_standards} standards from master registry.")

    # 2. Check for existing checkpoint
    is_codes: list[str] = []
    titles: list[str] = []
    embeddings_list: list[np.ndarray] = []
    start_idx = 0

    if chk_meta.exists() and chk_emb.exists():
        try:
            saved_meta = json.loads(chk_meta.read_text(encoding="utf-8"))
            saved_arr = np.load(str(chk_emb))
            if len(saved_meta["is_codes"]) == len(saved_arr):
                is_codes = saved_meta["is_codes"]
                titles = saved_meta["titles"]
                embeddings_list = [saved_arr]
                start_idx = len(is_codes)
                print(f">> Resuming from checkpoint: {start_idx} / {total_standards} ({start_idx / total_standards * 100:.1f}%)")
        except Exception as e:
            print(f">> Checkpoint corrupted or unreadable ({e}), starting fresh.")
            is_codes = []
            titles = []
            embeddings_list = []
            start_idx = 0

    if start_idx >= total_standards:
        print(">> All standards already encoded in checkpoint! Finalizing index...")
    else:
        # 3. Load BGE-M3 Embedder
        if embedder_model is not None:
            model = embedder_model
            print(">> Using in-memory BGE-M3 embedder model from FastAPI server...")
        else:
            print(">> Loading BGE-M3 embedder model...")
            model = get_embedder()
        print(">> Model ready. Beginning batch encoding...")

        start_time = time.time()
        last_checkpoint = start_idx
        pending_texts: list[str] = []
        pending_codes: list[str] = []
        pending_titles: list[str] = []

        for i in range(start_idx, total_standards):
            row = rows[i]
            code = str(row["is_code"]).strip()
            title = str(row["title"] or "").strip()
            scope = str(row["scope"] or "").strip()[:500]
            enriched = f"Indian Standard {code}: {title}. Scope: {scope}"

            pending_texts.append(enriched)
            pending_codes.append(code)
            pending_titles.append(title)

            # Process in batches
            if len(pending_texts) >= BATCH_SIZE or i == total_standards - 1:
                batch_embs = model.encode(
                    pending_texts,
                    batch_size=len(pending_texts),
                    show_progress_bar=False,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                ).astype(np.float32)

                embeddings_list.append(batch_embs)
                is_codes.extend(pending_codes)
                titles.extend(pending_titles)

                pending_texts = []
                pending_codes = []
                pending_titles = []

                # Periodic Checkpointing & Status Update
                completed = len(is_codes)
                # Write lightweight status file every batch so UI/Admin can see real-time progress
                update_status(completed, total_standards, start_time, status="RUNNING")

                if (completed - last_checkpoint) >= CHECKPOINT_INTERVAL or completed == total_standards:
                    last_checkpoint = completed
                    combined_arr = np.concatenate(embeddings_list, axis=0)
                    np.save(str(chk_emb), combined_arr)
                    chk_meta.write_text(
                        json.dumps({"is_codes": is_codes, "titles": titles}),
                        encoding="utf-8",
                    )
                    embeddings_list = [combined_arr]
                    pct = (completed / total_standards) * 100
                    elapsed = (time.time() - start_time) / 60
                    print(f"[{time.strftime('%H:%M:%S')}] Checkpoint: {completed}/{total_standards} ({pct:.1f}%) | Elapsed: {elapsed:.1f}m", flush=True)
                    gc.collect()

    # 4. Build FAISS FlatIP Index
    print(">> Building final 1024-d FAISS index...")
    full_embeddings = np.concatenate(embeddings_list, axis=0)
    dim = full_embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(full_embeddings)
    print(f">> Index built with {index.ntotal} vectors of dimension {dim}.")

    # 5. Atomic Save to Production Directory
    print(f">> Saving production index artifacts to {OUTPUT_DIR}...")
    faiss.write_index(index, str(OUTPUT_DIR / "dense_index.faiss"))
    meta_dict = {"is_codes": is_codes, "titles": titles}
    (OUTPUT_DIR / "dense_metadata.json").write_text(
        json.dumps(meta_dict, indent=2), encoding="utf-8"
    )

    update_status(total_standards, total_standards, time.time(), status="COMPLETED")
    print("=" * 80)
    print(">> FULL BGE-M3 DENSE INDEX BUILD SUCCESSFULLY COMPLETED!")
    print(f">> Total standards indexed: {len(is_codes)}")
    print(f">> Artifacts: {OUTPUT_DIR / 'dense_index.faiss'} & {OUTPUT_DIR / 'dense_metadata.json'}")
    print("=" * 80)

    if live_orchestrator is not None:
        from src.retrieval.faiss_vector_indexer import FAISSDenseIndex
        live_orchestrator.dense_index = FAISSDenseIndex.load(OUTPUT_DIR)
        print(">> Live search orchestrator dense index updated in memory!")


def main():
    run_indexing()


if __name__ == "__main__":
    main()
