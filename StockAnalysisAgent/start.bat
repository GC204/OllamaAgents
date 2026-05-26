@echo off
cd /d "%~dp0"

echo Starting Stock Advisor Agent...
echo.

REM If you named your virtual env differently, update `venv\Scripts\activate` below.
start "Stock Advisor - Backend" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python run.py"
timeout /t 3 /nobreak >nul

start "Stock Advisor - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Close the backend and frontend windows to stop, or run stop.bat
pause
