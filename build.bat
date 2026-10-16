@echo off
setlocal enabledelayedexpansion

echo ==============================================================================
echo [SMART RAILWAY RESERVATION] Visual C++ x64 Build System
echo Team ID: OSDBMS-V-2026-T281
echo ==============================================================================

set VCVARS="C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
if not exist %VCVARS% (
    set VCVARS="C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
)

if not exist %VCVARS% (
    echo [ERROR] Could not find Visual Studio 2022 vcvarsall.bat.
    echo Please ensure Visual Studio or Build Tools 2022 is installed.
    exit /b 1
)

echo [*] Initializing MSVC x64 Environment...
call %VCVARS% x64 >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to initialize MSVC x64 environment.
    exit /b 1
)

set MYSQL_INC="C:\Program Files\MySQL\MySQL Server 8.0\include"
set MYSQL_LIB="C:\Program Files\MySQL\MySQL Server 8.0\lib"
set MYSQL_DLL="C:\Program Files\MySQL\MySQL Server 8.0\lib\libmysql.dll"

if not exist %MYSQL_INC% (
    echo [ERROR] MySQL include directory not found at %MYSQL_INC%
    exit /b 1
)

echo [*] Copying libmysql.dll to workspace root...
if exist %MYSQL_DLL% (
    copy /y %MYSQL_DLL% .\libmysql.dll >nul
)

echo [*] Compiling Main Server Application (smart_railway.exe)...
cl /nologo /std:c++17 /EHsc /O2 /Iinclude /I%MYSQL_INC% ^
    src\main.cpp src\db_manager.cpp src\scheduler.cpp src\telemetry.cpp ^
    /link /LIBPATH:%MYSQL_LIB% libmysql.lib ws2_32.lib crypt32.lib ^
    /out:smart_railway.exe

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Compilation of smart_railway.exe failed!
    exit /b 1
)

echo [*] Compiling Concurrency Test Suite (concurrency_test.exe)...
cl /nologo /std:c++17 /EHsc /O2 /Iinclude /I%MYSQL_INC% ^
    tests\concurrency_test.cpp src\db_manager.cpp src\scheduler.cpp src\telemetry.cpp ^
    /link /LIBPATH:%MYSQL_LIB% libmysql.lib ws2_32.lib crypt32.lib ^
    /out:concurrency_test.exe

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Compilation of concurrency_test.exe failed!
    exit /b 1
)

:: Clean up temporary object files
del /q *.obj >nul 2>&1

echo ==============================================================================
echo [SUCCESS] Build completed successfully!
echo   - smart_railway.exe (Core C++ Web Server ^& OS Scheduler Daemon)
echo   - concurrency_test.exe (Automated Concurrency ^& Race Condition Test Suite)
echo ==============================================================================
