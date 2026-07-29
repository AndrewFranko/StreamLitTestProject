#!/bin/bash

echo "=================================="
echo "FactoryOps AI - Full Stack"
echo "=================================="
echo ""

# Kill any existing processes
pkill -f "serve.py" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true

sleep 2

# Start Agent API on 8000
echo "Starting Agent API Server on port 8000..."
python serve.py &
SERVE_PID=$!

# Start Streamlit on 8501
echo "Starting Streamlit Web UI on port 8501..."
streamlit run app.py --server.port 8501 --server.address localhost &
STREAMLIT_PID=$!

sleep 5

echo ""
echo "=================================="
echo "✅ All Services Running"
echo "=================================="
echo ""
echo "Web UI (Streamlit):"
echo "  http://localhost:8501"
echo ""
echo "Agent API (FastAPI):"
echo "  http://localhost:8000/docs"
echo "  http://localhost:8000/health"
echo ""
echo "Agent Endpoints:"
echo "  http://localhost:8000/operator/invoke"
echo "  http://localhost:8000/engineer/invoke"
echo "  http://localhost:8000/supervisor/invoke"
echo "  http://localhost:8000/plant_manager/invoke"
echo ""
echo "LangSmith Studio Connect:"
echo "  https://eu.smith.langchain.com/o/42958419-e9fe-43a7-bcdb-44c4a960ee90/studio/connect?mode=graph"
echo "  Base URL: http://localhost:8000"
echo ""
echo "Process IDs:"
echo "  Agent API: $SERVE_PID"
echo "  Streamlit: $STREAMLIT_PID"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================="
echo ""

# Wait for processes
wait
