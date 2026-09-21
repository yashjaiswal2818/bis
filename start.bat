@echo off
title BIS Recommendation Engine Launcher
cd /d "%~dp0"
echo Starting Indian Standards Recommendation Engine...

:: Prevent OpenMP runtime conflict segfaults between FAISS and PyTorch
set OMP_NUM_THREADS=1
set KMP_DUPLICATE_LIB_OK=TRUE

if exist backend\venv\Scripts\python.exe (
    backend\venv\Scripts\python.exe start.py
) else (
    python start.py
)
pause
