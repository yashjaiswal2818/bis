"""Unified Application Launcher.

Boots the FastAPI backend (:8000) and lightweight frontend (:3000),
opens the browser to http://localhost:3000, and manages graceful shutdown.
"""
from __future__ import annotations

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = ROOT_DIR / "backend" / "venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
if not PYTHON_EXE.exists():
    PYTHON_EXE = Path(sys.executable)


def main():
    print("=" * 65)
    print("  INDIAN STANDARDS (BIS) RECOMMENDATION ENGINE: LAUNCHER")
    print("=" * 65)

    # 1. Verify indexes exist
    faiss_index = ROOT_DIR / "backend" / "data" / "index" / "dense_index.faiss"
    if not faiss_index.exists():
        print("\n[Setup] Precomputed indexes not found. Building indexes first...")
        subprocess.run([str(PYTHON_EXE), "backend/build_indices.py"], cwd=ROOT_DIR, check=True)

    # 2. Launch Backend (FastAPI on :8000)
    print("\n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        [
            str(PYTHON_EXE),
            "-m",
            "uvicorn",
            "src.api.fastapi_application:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=ROOT_DIR / "backend",
    )

    # 3. Launch Frontend (Static server on :3000)
    print("[2/2] Starting Test Frontend on http://localhost:3000 ...")
    frontend_proc = subprocess.Popen(
        [str(PYTHON_EXE), "frontend/start_frontend.py"],
        cwd=ROOT_DIR,
    )

    # Give backend a couple seconds to warm up
    time.sleep(2)
    print("\n" + "=" * 65)
    print("  SYSTEM READY!")
    print("  • Web UI:      http://localhost:3000")
    print("  • API Docs:    http://127.0.0.1:8000/docs")
    print("  Press Ctrl+C to stop both servers.")
    print("=" * 65)

    try:
        webbrowser.open("http://localhost:3000")
    except Exception:
        pass

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("[Shutdown] Servers stopped cleanly.")


if __name__ == "__main__":
    main()
