#!/bin/bash

# FactoryOps AI - Local Deployment Startup Script
# Bash/Shell Script for Unix/Linux/macOS

echo ""
echo "====================================================="
echo "FactoryOps AI - Manufacturing Assistant"
echo "Local Deployment Startup"
echo "====================================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file with GOOGLE_API_KEY"
    exit 1
fi

# Check Python installation
echo "[1/3] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.10+ from https://www.python.org"
    exit 1
fi
python3 --version
echo "[OK] Python found"

echo ""
echo "[2/3] Installing dependencies from requirements.txt..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "[OK] Dependencies installed"

echo ""
echo "[3/3] Starting Streamlit app..."
echo ""
echo "====================================================="
echo "FactoryOps AI is launching..."
echo "Open your browser to: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo "====================================================="
echo ""

# Run Streamlit
streamlit run src/ui/app.py
