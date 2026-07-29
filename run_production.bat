@echo off
REM Production localhost deployment script for FactoryOps AI

echo.
echo ========================================
echo FactoryOps AI - Production Deployment
echo ========================================
echo.

REM Check Python
python --version

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Verify configuration
echo.
echo Verifying configuration...
python << PYEOF
import sys
sys.path.insert(0, 'src')

from langsmith_config import get_langsmith_status
from config import settings

status = get_langsmith_status()
print(f"OK: App Name: {settings.app_name}")
print(f"OK: Environment: {settings.app_env}")
print(f"OK: Model: {settings.model_name}")
print(f"OK: LangSmith: {'Enabled' if status['tracing_enabled'] else 'Disabled'}")
print(f"OK: Project: {status['project_name']}")
PYEOF

echo.
echo ========================================
echo LAUNCHING STREAMLIT APP
echo ========================================
echo.
echo App will be available at:
echo   ^> http://localhost:8501
echo.
echo LangSmith Studio:
echo   ^> https://smith.langchain.com/studio?projectName=Factory
echo.
echo Press Ctrl+C to stop the server
echo.

REM Launch Streamlit
streamlit run app.py --server.port 8501 --server.address localhost
pause
