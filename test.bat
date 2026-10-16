@echo off
setlocal
echo ==============================================================================
echo [SMART RAILWAY RESERVATION] Running Concurrency & Race Condition Tests
echo Team ID: OSDBMS-V-2026-T281
echo ==============================================================================

if not exist concurrency_test.exe (
    echo [*] Test executable not found. Compiling first using build.bat...
    call build.bat
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Build failed.
        pause
        exit /b 1
    )
)

.\concurrency_test.exe
pause
