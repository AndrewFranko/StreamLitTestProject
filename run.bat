@echo off
REM FactoryOps AI - Local Deployment Startup Script
REM Windows Batch File

echo.
echo =====================================================
echo FactoryOps AI - Manufacturing Assistant
echo Local Deployment Startup
echo =====================================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create .env file with GOOGLE_API_KEY
    pause
    exit /b 1
)

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)
echo [OK] Python found

echo.
echo [2/3] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

echo.
echo [3/3] Starting Streamlit app...
echo.
echo =====================================================
echo FactoryOps AI is launching...
echo Open your browser to: http://localhost:8501
echo Press Ctrl+C to stop the server
echo =====================================================
echo.

REM Run Streamlit - use absolute path for the app
cd /d "%~dp0"
streamlit run src\ui\app.py

pause
