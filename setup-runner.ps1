# GitHub Actions Self-Hosted Runner Setup Script for Windows
# Run as Administrator

param(
    [string]$RepoUrl,
    [string]$Token,
    [string]$RunnerName = "streamlit-deployment-runner"
)

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-ErrorCustom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Check if running as Administrator
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-ErrorCustom "This script must be run as Administrator!"
    exit 1
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "GitHub Actions Self-Hosted Runner Setup (Windows)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$RUNNER_VERSION = "2.319.0"
$RUNNER_DIR = "$env:USERPROFILE\github-runner"
$ARCH = if ([Environment]::Is64BitProcess) { "x64" } else { "x86" }

# Collect user input
Write-Step "Collecting configuration..."

if ([string]::IsNullOrEmpty($RepoUrl)) {
    $RepoUrl = Read-Host "Enter your GitHub repository URL"
}

if ([string]::IsNullOrEmpty($Token)) {
    $Token = Read-Host "Enter your GitHub Personal Access Token or Runner Registration Token" -AsSecureString
    $Token = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($Token))
}

$RunnerNameInput = Read-Host "Enter a name for this runner (default: streamlit-deployment-runner)"
if (-not [string]::IsNullOrEmpty($RunnerNameInput)) {
    $RunnerName = $RunnerNameInput
}

# Create runner directory
Write-Step "Creating runner directory..."

if (-not (Test-Path $RUNNER_DIR)) {
    New-Item -ItemType Directory -Path $RUNNER_DIR -Force | Out-Null
    Write-Success "Created $RUNNER_DIR"
}
else {
    Write-Success "Directory already exists: $RUNNER_DIR"
}

Set-Location $RUNNER_DIR

# Download GitHub Actions Runner
Write-Step "Downloading GitHub Actions Runner v$RUNNER_VERSION..."

$DownloadUrl = "https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/actions-runner-win-$ARCH-$RUNNER_VERSION.zip"
$ZipFile = "actions-runner-win-$ARCH-$RUNNER_VERSION.zip"

if (Test-Path $ZipFile) {
    Write-Success "Runner archive already exists"
}
else {
    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipFile -ErrorAction Stop
        Write-Success "Downloaded runner"
    }
    catch {
        Write-ErrorCustom "Failed to download runner: $_"
        exit 1
    }
}

# Extract runner
Write-Step "Extracting runner files..."

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($ZipFile, ".")
    Write-Success "Runner extracted"
}
catch {
    Write-ErrorCustom "Failed to extract runner: $_"
    exit 1
}

# Configure the runner
Write-Step "Configuring the runner..."
Write-Host "The configuration wizard will now start." -ForegroundColor Yellow
Write-Host "This will connect your runner to: $RepoUrl"
Write-Host ""

& .\config.cmd `
    --url $RepoUrl `
    --token $Token `
    --name $RunnerName `
    --runnergroup "Default" `
    --labels "windows,streamlit,deployment,github-actions" `
    --unattended `
    --work "_work"

if ($LASTEXITCODE -ne 0) {
    Write-ErrorCustom "Failed to configure runner"
    exit 1
}

Write-Success "Runner configured"

# Install as Windows Service
Write-Step "Installing as Windows Service..."

try {
    & .\svc.cmd install
    Write-Success "Service installed"
}
catch {
    Write-ErrorCustom "Failed to install service: $_"
    exit 1
}

# Start the service
Write-Step "Starting service..."

try {
    & .\svc.cmd start
    Write-Success "Service started"
}
catch {
    Write-ErrorCustom "Failed to start service: $_"
    exit 1
}

# Check service status
Write-Step "Checking service status..."
& .\svc.cmd status

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Success "GitHub Actions Runner Setup Complete!"
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Verify the runner is online in GitHub:"
Write-Host "   Settings → Actions → Runners (in your repository)"
Write-Host ""
Write-Host "2. Check runner status:"
Write-Host "   & '.\svc.cmd' status"
Write-Host ""
Write-Host "3. View Event Viewer logs for the service:"
Write-Host "   Event Viewer → Windows Logs → Application"
Write-Host ""
Write-Host "4. The runner is now listening for jobs from:"
Write-Host "   $RepoUrl"
Write-Host ""
