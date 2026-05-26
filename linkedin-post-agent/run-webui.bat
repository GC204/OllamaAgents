@echo off
echo ====================================
echo LinkedIn Post Generator - Web UI
echo ====================================
echo.

if not exist venv (
    echo Error: Virtual environment not found
    echo Run setup.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Starting web server...
echo Open http://localhost:8000 in your browser
echo.

python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
