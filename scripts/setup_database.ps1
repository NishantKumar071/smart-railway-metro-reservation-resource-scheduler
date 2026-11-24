# =============================================================================
# SmartRail AI+ — Database Setup PowerShell Script
# =============================================================================
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " SmartRail AI+ — Database Initialization" -ForegroundColor Cyan
Write-Host "================================================================="

$mysqlExe = "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
if (-not (Test-Path $mysqlExe)) {
    $mysqlExe = "mysql"
}

$dbHost = "localhost"
$dbPort = 3306
$dbUser = "root"
$dbPass = Read-Host "Enter MySQL root password (press Enter if none)"

$projectRoot = Split-Path -Parent $PSScriptRoot
$schemaPath = Join-Path $projectRoot "database\schema.sql"
$seedPath = Join-Path $projectRoot "database\seed_data.sql"
$aiPath = Join-Path $projectRoot "database\ai_history.sql"

Write-Host "`n[1/3] Running schema.sql..." -ForegroundColor Yellow
if ($dbPass) {
    & $mysqlExe -h $dbHost -P $dbPort -u $dbUser "-p$dbPass" -e "source $schemaPath"
} else {
    & $mysqlExe -h $dbHost -P $dbPort -u $dbUser -e "source $schemaPath"
}

Write-Host "[2/3] Running seed_data.sql..." -ForegroundColor Yellow
if ($dbPass) {
    & $mysqlExe -h $dbHost -P $dbPort -u $dbUser "-p$dbPass" -e "source $seedPath"
} else {
    & $mysqlExe -h $dbHost -P $dbPort -u $dbUser -e "source $seedPath"
}

Write-Host "[3/3] Running ai_history.sql..." -ForegroundColor Yellow
if ($dbPass) {
    & $mysqlExe -h $dbHost -P $dbPort -u $dbUser "-p$dbPass" -e "source $aiPath"
} else {
    & $mysqlExe -h $dbHost -P $dbPort -u $dbUser -e "source $aiPath"
}

Write-Host "`nDatabase setup finished successfully!" -ForegroundColor Green
