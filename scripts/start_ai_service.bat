@echo off
REM =============================================================================
REM SmartRail AI+ — Start Python AI Service
REM =============================================================================
echo Starting SmartRail AI+ AI Service on http://localhost:8000 ...
cd /d "%~dp0..\ai-service"
python main.py
pause
