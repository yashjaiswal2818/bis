@echo off
title BIS Recommendation Engine Launcher
cd /d "%~dp0"
echo Starting Indian Standards Recommendation Engine...
if exist backend\venv\Scripts\python.exe (
    backend\venv\Scripts\python.exe start.py
) else (
    python start.py
)
pause
