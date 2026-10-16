@echo off
setlocal
echo ==============================================================================
echo [SMART RAILWAY RESERVATION] Starting Interactive CLI Viva Mode
echo Team ID: OSDBMS-V-2026-T281
echo Leader: Nishant Kumar ^| Member: Robert Sandi Thomas
echo ==============================================================================

if not exist smart_railway.exe (
    echo [*] Executable not found. Compiling first using build.bat...
    call build.bat
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Build failed.
        pause
        exit /b 1
    )
)

.\smart_railway.exe --cli
pause
