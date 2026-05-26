@echo off
echo Starting LinkedIn Post Generator Agent...
echo.

if not exist venv (
    echo Error: Virtual environment not found
    echo Run setup.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
python main.py
