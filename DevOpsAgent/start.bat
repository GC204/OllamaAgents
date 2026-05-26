@echo off
REM DevOps Agent - Start Application
REM This batch file starts both backend and frontend servers

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   DevOps CI/CD Agent - Starting
echo ========================================
echo.

REM Check if backend directory exists
if not exist "backend" (
    echo ERROR: backend directory not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "frontend" (
    echo ERROR: frontend directory not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if Python virtual environment exists
if not exist "backend\venv" (
    echo Creating Python virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

REM Start Backend Server
echo Starting Backend Server (FastAPI on port 8000)...
echo.
start "DevOps Agent - Backend" cmd /k "cd backend && venv\Scripts\activate && pip install -r requirements.txt -q && python -m uvicorn app:app --reload --port 8000"

REM Wait for backend to start
timeout /t 5 /nobreak

REM Check if Node modules are installed in frontend
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install -q
    cd ..
)

REM Start Frontend Server
echo.
echo Starting Frontend Server (React on port 5173)...
echo.
start "DevOps Agent - Frontend" cmd /k "cd frontend && npm run dev"

REM Wait for frontend to start
timeout /t 3 /nobreak

REM Open browser
echo.
echo Opening application in browser...
timeout /t 2 /nobreak
start http://localhost:5173

echo.
echo ========================================
echo   Application Started Successfully!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Two terminal windows should have opened:
echo   1. Backend (FastAPI)
echo   2. Frontend (React Dev Server)
echo.
echo To stop the application, run: stop.bat
echo.
pause
