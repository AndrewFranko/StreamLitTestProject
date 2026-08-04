#!/bin/bash

# GitHub Actions Self-Hosted Runner Setup Script
# This script automates the installation and configuration of a GitHub Actions runner

set -e

echo "================================================"
echo "GitHub Actions Self-Hosted Runner Setup"
echo "================================================"
echo ""

# Configuration
RUNNER_VERSION="2.319.0"
RUNNER_DIR="${HOME}/github-runner"
REPO_URL=""
RUNNER_TOKEN=""
RUNNER_NAME="streamlit-deployment-runner"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Linux or macOS
if [[ ! "$OSTYPE" =~ ^linux || "$OSTYPE" =~ ^darwin ]]; then
    echo -e "${RED}This script is designed for Linux and macOS. For Windows, use setup-runner.ps1${NC}"
    exit 1
fi

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

# Step 1: Collect user input
print_step "Collecting configuration..."

if [ -z "$GITHUB_REPO_URL" ]; then
    read -p "Enter your GitHub repository URL (e.g., https://github.com/username/repo): " REPO_URL
else
    REPO_URL=$GITHUB_REPO_URL
fi

if [ -z "$GITHUB_RUNNER_TOKEN" ]; then
    read -sp "Enter your GitHub Personal Access Token (or Runner Registration Token): " RUNNER_TOKEN
    echo ""
else
    RUNNER_TOKEN=$GITHUB_RUNNER_TOKEN
fi

read -p "Enter a name for this runner (default: streamlit-deployment-runner): " -e -i "$RUNNER_NAME" RUNNER_NAME

# Step 2: Install dependencies
print_step "Installing required dependencies..."

# Detect package manager
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y curl wget git python3.10 python3-pip
    print_success "Installed via apt"
elif command -v brew &> /dev/null; then
    brew install git python curl
    print_success "Installed via homebrew"
else
    print_error "Could not find package manager. Please install curl, git, and python3.10 manually."
    exit 1
fi

# Step 3: Create runner directory
print_step "Creating runner directory..."

if [ ! -d "$RUNNER_DIR" ]; then
    mkdir -p "$RUNNER_DIR"
    print_success "Created $RUNNER_DIR"
else
    print_success "Directory already exists: $RUNNER_DIR"
fi

cd "$RUNNER_DIR"

# Step 4: Download GitHub Actions Runner
print_step "Downloading GitHub Actions Runner v${RUNNER_VERSION}..."

# Determine architecture
ARCH=$(uname -m)
if [ "$ARCH" == "x86_64" ]; then
    RUNNER_ARCH="x64"
elif [ "$ARCH" == "aarch64" ]; then
    RUNNER_ARCH="arm64"
else
    print_error "Unsupported architecture: $ARCH"
    exit 1
fi

OS_TYPE="linux"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="osx"
fi

DOWNLOAD_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-${OS_TYPE}-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"

if [ -f "actions-runner-${OS_TYPE}-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz" ]; then
    print_success "Runner archive already downloaded"
else
    wget "$DOWNLOAD_URL" -O "actions-runner-${OS_TYPE}-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
    print_success "Downloaded runner"
fi

# Step 5: Extract runner
print_step "Extracting runner files..."

tar xzf "actions-runner-${OS_TYPE}-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
print_success "Runner extracted"

# Step 6: Configure the runner
print_step "Configuring the runner..."

echo ""
echo "The configuration wizard will now start."
echo "This will connect your runner to: $REPO_URL"
echo ""

./config.sh --url "$REPO_URL" \
            --token "$RUNNER_TOKEN" \
            --name "$RUNNER_NAME" \
            --runnergroup "Default" \
            --labels "linux,streamlit,deployment,github-actions" \
            --work "_work" \
            --unattended

print_success "Runner configured"

# Step 7: Install as systemd service (if available)
if command -v systemctl &> /dev/null; then
    print_step "Setting up systemd service..."

    # Create systemd service file
    SERVICE_FILE="/etc/systemd/system/github-runner.service"

    sudo bash -c cat > "$SERVICE_FILE" << EOF
[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$RUNNER_DIR
ExecStart=$RUNNER_DIR/run.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable github-runner
    sudo systemctl start github-runner

    print_success "systemd service installed and started"

    # Verify service status
    echo ""
    print_step "Checking service status..."
    sudo systemctl status github-runner --no-pager

else
    print_step "systemd not available. Starting runner manually..."

    # Run in background with nohup
    nohup ./run.sh > runner.log 2>&1 &
    RUNNER_PID=$!

    print_success "Runner started with PID: $RUNNER_PID"
    echo "To view logs: tail -f $RUNNER_DIR/runner.log"
fi

# Step 8: Verification
echo ""
echo "================================================"
print_success "GitHub Actions Runner Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Verify the runner is online in GitHub:"
echo "   Settings → Actions → Runners (in your repository)"
echo ""
echo "2. Check runner status:"
if command -v systemctl &> /dev/null; then
    echo "   sudo systemctl status github-runner"
else
    echo "   tail -f $RUNNER_DIR/runner.log"
fi
echo ""
echo "3. View runner diagnostic logs:"
echo "   tail -f $RUNNER_DIR/_diag/Runner_*"
echo ""
echo "4. The runner is now listening for jobs from:"
echo "   $REPO_URL"
echo ""
