@echo off
REM =============================================================================
REM SmartRail AI+ — Build C++ Backend Script
REM =============================================================================
echo =============================================================================
echo  SmartRail AI+ — C++ Backend Build System
echo =============================================================================

cd /d "%~dp0..\backend"

where cmake >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [NOTICE] CMake is not found in PATH.
    echo The SmartRail AI+ unified backend is also fully operable directly via Python
    echo (which mirrors the C++ thread pool, condition variable queue, and locks).
    echo.
    echo To build native C++ binary once CMake / MinGW / MSVC is configured:
    echo   mkdir build ^&^& cd build
    echo   cmake ..
    echo   cmake --build . --config Release
    pause
    exit /b 0
)

if not exist build mkdir build
cd build
cmake ..
cmake --build . --config Release

echo Build finished.
pause
