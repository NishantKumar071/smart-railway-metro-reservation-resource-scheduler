@echo off
REM =============================================================================
REM SmartRail AI+ — Start Backend API Service
REM =============================================================================
echo Starting SmartRail AI+ Backend on http://localhost:8080 ...
cd /d "%~dp0..\backend"
python main.py
pause
