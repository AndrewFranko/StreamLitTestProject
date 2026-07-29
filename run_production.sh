#!/bin/bash
# Production localhost deployment script for FactoryOps AI

set -e

echo "========================================"
echo "FactoryOps AI - Production Deployment"
echo "========================================"
echo ""

# Check Python
python --version

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Verify configuration
echo ""
echo "Verifying configuration..."
python << 'PYEOF'
import sys
sys.path.insert(0, 'src')

from langsmith_config import get_langsmith_status
from config import settings

status = get_langsmith_status()
print(f"✓ App Name: {settings.app_name}")
print(f"✓ Environment: {settings.app_env}")
print(f"✓ Model: {settings.model_name}")
print(f"✓ LangSmith: {'Enabled' if status['tracing_enabled'] else 'Disabled'}")
print(f"✓ Project: {status['project_name']}")
PYEOF

echo ""
echo "========================================"
echo "LAUNCHING STREAMLIT APP"
echo "========================================"
echo ""
echo "App will be available at:"
echo "  ▶ http://localhost:8501"
echo ""
echo "LangSmith Studio:"
echo "  ▶ https://smith.langchain.com/studio?projectName=Factory"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Launch Streamlit
streamlit run app.py --server.port 8501 --server.address localhost
