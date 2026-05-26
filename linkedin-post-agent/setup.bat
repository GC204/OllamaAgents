@echo off
echo ====================================
echo LinkedIn Post Generator - Setup
echo ====================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    echo Make sure Python 3.9+ is installed
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/4] Installing Playwright browsers...
playwright install chromium

echo.
echo ====================================
echo Setup complete!
echo ====================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env
echo 2. Edit .env with your LinkedIn credentials
echo 3. Make sure Ollama is running: ollama serve
echo 4. Install a model: ollama pull llama3.2
echo 5. Run the agent: python main.py
echo.
pause
