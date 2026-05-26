@echo off
REM DevOps Agent - Stop Application
REM This batch file stops both backend and frontend servers

echo.
echo ========================================
echo   DevOps CI/CD Agent - Stopping
echo ========================================
echo.

REM Kill processes on port 8000 (Backend)
echo Stopping Backend Server (port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /PID %%a /F /T >nul 2>&1
)

if %errorlevel% equ 0 (
    echo ✓ Backend stopped
) else (
    echo ℹ Backend not running or already stopped
)

REM Kill processes on port 5173 (Frontend)
echo Stopping Frontend Server (port 5173)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do (
    taskkill /PID %%a /F /T >nul 2>&1
)

if %errorlevel% equ 0 (
    echo ✓ Frontend stopped
) else (
    echo ℹ Frontend not running or already stopped
)

echo.
echo ========================================
echo   Application Stopped
echo ========================================
echo.
echo To start the application again, run: start.bat
echo.
pause
