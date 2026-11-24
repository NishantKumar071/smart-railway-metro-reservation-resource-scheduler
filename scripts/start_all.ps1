Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host " SmartRail AI+ — Master Launcher" -ForegroundColor Cyan
Write-Host "================================================================="

$projectRoot = Split-Path -Parent $PSScriptRoot
$aiDir = Join-Path $projectRoot "ai-service"
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"

Write-Host "Starting Python AI Service on port 8000..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k", "cd /d `"$aiDir`" && python main.py"

Write-Host "Starting Backend Engine on port 8080..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k", "cd /d `"$backendDir`" && python main.py"

Write-Host "Starting Frontend Web Server on port 3000..." -ForegroundColor Yellow
Start-Process cmd.exe -ArgumentList "/k", "cd /d `"$frontendDir`" && python -m http.server 3000"

Start-Sleep -Seconds 3

Write-Host "All services started! Opening http://localhost:3000..." -ForegroundColor Green
Start-Process "http://localhost:3000"
