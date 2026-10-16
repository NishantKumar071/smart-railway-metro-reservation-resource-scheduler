@echo off
setlocal
echo ==============================================================================
echo [SMART RAILWAY RESERVATION] Database Setup Utility
echo Team ID: OSDBMS-V-2026-T281
echo ==============================================================================

set MYSQL_BIN="C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
set DB_USER=root
set DB_PASS=Root@123

if not exist %MYSQL_BIN% (
    echo [ERROR] MySQL binary not found at %MYSQL_BIN%
    echo Please edit this script if your MySQL Server is installed in a custom location.
    pause
    exit /b 1
)

echo [*] Applying Schema (sql\schema.sql)...
%MYSQL_BIN% -u %DB_USER% -p%DB_PASS% < sql\schema.sql
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to apply schema.
    pause
    exit /b 1
)

echo [*] Seeding Real Indian Railways Data (sql\seed_real_data.sql)...
%MYSQL_BIN% -u %DB_USER% -p%DB_PASS% < sql\seed_real_data.sql
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to seed database.
    pause
    exit /b 1
)

echo [SUCCESS] Database smart_railway_db configured and seeded successfully!
pause
