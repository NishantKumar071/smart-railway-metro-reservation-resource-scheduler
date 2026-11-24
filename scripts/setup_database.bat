@echo off
REM =============================================================================
REM SmartRail AI+ — Database Initialization Script
REM =============================================================================
setlocal enabledelayedexpansion

echo =============================================================================
echo  SmartRail AI+ — Safe Database Setup & Migration
echo =============================================================================

set MYSQL_PATH="C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
if not exist %MYSQL_PATH% (
    set MYSQL_PATH=mysql
)

set DB_HOST=localhost
set DB_PORT=3306
set DB_USER=root

echo Please enter your MySQL root password (leave blank if no password):
set /p DB_PASS=

echo.
echo [1/3] Creating schema and tables...
%MYSQL_PATH% -h %DB_HOST% -P %DB_PORT% -u %DB_USER% %DB_PASS% < "%~dp0..\database\schema.sql"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to execute schema.sql. Please check your credentials and MySQL server status.
    pause
    exit /b %ERRORLEVEL%
)

echo [2/3] Seeding demonstration stations, trains, and inventory...
%MYSQL_PATH% -h %DB_HOST% -P %DB_PORT% -u %DB_USER% %DB_PASS% < "%~dp0..\database\seed_data.sql"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to execute seed_data.sql.
    pause
    exit /b %ERRORLEVEL%
)

echo [3/3] Loading synthetic AI training history tables...
%MYSQL_PATH% -h %DB_HOST% -P %DB_PORT% -u %DB_USER% %DB_PASS% < "%~dp0..\database\ai_history.sql"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to execute ai_history.sql.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo =============================================================================
echo  Database Setup Completed Successfully!
echo =============================================================================
pause
