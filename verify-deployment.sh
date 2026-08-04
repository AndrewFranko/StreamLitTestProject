#!/bin/bash

# Deployment Verification Script
# This script verifies that the application is running correctly after deployment

set -e

STREAMLIT_PORT=8501
STREAMLIT_HOST="localhost"
MAX_RETRIES=30
RETRY_INTERVAL=2

echo "================================================"
echo "Application Deployment Verification"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print messages
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Step 1: Check if process is running
print_step "Checking if Streamlit process is running..."

if pgrep -f "streamlit run" > /dev/null; then
    STREAMLIT_PID=$(pgrep -f "streamlit run")
    print_success "Streamlit process found (PID: $STREAMLIT_PID)"
else
    print_error "Streamlit process not found!"
    exit 1
fi

# Step 2: Check if port is listening
print_step "Checking if port $STREAMLIT_PORT is listening..."

if netstat -tuln 2>/dev/null | grep -q ":$STREAMLIT_PORT " || ss -tuln 2>/dev/null | grep -q ":$STREAMLIT_PORT "; then
    print_success "Port $STREAMLIT_PORT is listening"
else
    print_warning "Port $STREAMLIT_PORT is not yet listening (may be starting)"
fi

# Step 3: Wait for application to respond
print_step "Waiting for application to respond on http://$STREAMLIT_HOST:$STREAMLIT_PORT..."

RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f "http://$STREAMLIT_HOST:$STREAMLIT_PORT" > /dev/null 2>&1; then
        print_success "Application is responding"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep $RETRY_INTERVAL
done

echo ""

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    print_error "Application did not respond after $((MAX_RETRIES * RETRY_INTERVAL)) seconds"
    exit 1
fi

# Step 4: Get HTTP response code
print_step "Checking HTTP response..."

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$STREAMLIT_HOST:$STREAMLIT_PORT")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "HTTP response code: $HTTP_CODE"
else
    print_warning "HTTP response code: $HTTP_CODE (expected 200)"
fi

# Step 5: Check application logs
print_step "Checking application logs..."

if [ -f "logs/app.log" ]; then
    LOG_LINES=$(tail -20 logs/app.log)

    if echo "$LOG_LINES" | grep -qi "error\|fail"; then
        print_warning "Errors found in recent logs:"
        echo "$LOG_LINES" | grep -i "error\|fail" || true
    else
        print_success "Application logs look healthy"
        echo ""
        echo "Recent log entries:"
        tail -5 logs/app.log
    fi
else
    print_warning "Log file not found: logs/app.log"
fi

# Step 6: Get application details
print_step "Application Details:"

echo ""
echo "  URL: http://$STREAMLIT_HOST:$STREAMLIT_PORT"
echo "  Process ID: $STREAMLIT_PID"
echo "  Port: $STREAMLIT_PORT"

# Get Python version
PYTHON_VERSION=$(python --version 2>&1)
echo "  Python: $PYTHON_VERSION"

# Get application uptime
PROCESS_START=$(ps -o lstart= -p $STREAMLIT_PID)
echo "  Started: $PROCESS_START"

# Get process memory usage
MEMORY=$(ps -o rss= -p $STREAMLIT_PID | awk '{printf "%0.2f MB", $1/1024}')
echo "  Memory: $MEMORY"

echo ""
echo "================================================"
print_success "Deployment Verification Complete!"
echo "================================================"
echo ""
echo "To access the application:"
echo "  • Open http://$STREAMLIT_HOST:$STREAMLIT_PORT in your browser"
echo "  • Or access from remote: http://<server-ip>:$STREAMLIT_PORT"
echo ""
echo "To view live logs:"
echo "  tail -f logs/app.log"
echo ""
echo "To stop the application:"
echo "  pkill -f 'streamlit run'"
echo ""
