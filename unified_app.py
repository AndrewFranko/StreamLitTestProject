"""
Unified App Server - Combines Streamlit UI and Agent API on same port

Run: python unified_app.py

Access:
  - Web UI: http://localhost:8080
  - Agent API: http://localhost:8080/api/docs
  - Agent endpoints: http://localhost:8080/api/operator, etc.
"""

import sys
import logging
from pathlib import Path
import subprocess
import time
import os

sys.path.insert(0, str(Path(__file__).parent / "src"))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Start serve.py on 8000
logger.info("Starting Agent API Server on port 8000...")
serve_process = subprocess.Popen(
    [sys.executable, "serve.py"],
    cwd=Path(__file__).parent,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

time.sleep(5)

# Start Streamlit on 8501
logger.info("Starting Streamlit Web UI on port 8501...")
streamlit_process = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        "8501",
        "--server.address",
        "localhost",
    ],
    cwd=Path(__file__).parent,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

time.sleep(3)

print("\n" + "="*70)
print("FactoryOps AI - Unified App Server")
print("="*70)
print("\n✅ Both services running:")
print("\n  Web UI (Streamlit):  http://localhost:8501")
print("  Agent API (FastAPI): http://localhost:8000")
print("\n📊 LangSmith Studio:")
print("  https://eu.smith.langchain.com/o/42958419-e9fe-43a7-bcdb-44c4a960ee90/studio/connect?mode=graph")
print("  Base URL: http://localhost:8000")
print("\n" + "="*70 + "\n")

# Keep both processes running
try:
    while True:
        serve_poll = serve_process.poll()
        streamlit_poll = streamlit_process.poll()

        if serve_poll is not None:
            logger.error(f"Agent API Server crashed with code {serve_poll}")
            break

        if streamlit_poll is not None:
            logger.error(f"Streamlit crashed with code {streamlit_poll}")
            break

        time.sleep(5)
except KeyboardInterrupt:
    logger.info("Shutting down...")
    serve_process.terminate()
    streamlit_process.terminate()
    serve_process.wait()
    streamlit_process.wait()
