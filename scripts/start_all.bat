@echo off
setlocal
cd /d "%~dp0.."

echo Starting SmartRail AI+ Application...

start "SmartRail-AI-Service" cmd.exe /k "cd /d "%~dp0..\ai-service" && python main.py"
start "SmartRail-Backend" cmd.exe /k "cd /d "%~dp0..\backend" && python main.py"
start "SmartRail-Frontend" cmd.exe /k "cd /d "%~dp0..\frontend" && python -m http.server 3000"

echo All three services have been launched in separate terminal windows.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:8080/docs
echo AI Svc:   http://localhost:8000/docs

timeout /t 3 /nobreak >nul
start http://localhost:3000
