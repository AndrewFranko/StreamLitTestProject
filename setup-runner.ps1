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
    Write-Host "PASS $Message" -ForegroundColor Green
}

function Write-ErrorCustom {
    param([string]$Message)
    Write-Host "FAIL $Message" -ForegroundColor Red
}

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-ErrorCustom "This script must be run as Administrator!"
    exit 1
}

Write-Host "GitHub Actions Self-Hosted Runner Setup (Windows)"
Write-Host ""

$RUNNER_VERSION = "2.319.0"
$RUNNER_DIR = "$env:USERPROFILE\github-runner"
$ARCH = if ([Environment]::Is64BitProcess) { "x64" } else { "x86" }
$CURRENT_DIR = Get-Location

Write-Host "Current directory: $CURRENT_DIR" -ForegroundColor Yellow
Write-Host "Runner will be installed to: $RUNNER_DIR" -ForegroundColor Yellow
Write-Host ""

Write-Step "Collecting configuration"

if ([string]::IsNullOrEmpty($RepoUrl)) {
    $RepoUrl = Read-Host "Enter GitHub repository URL"
}

if ([string]::IsNullOrEmpty($Token)) {
    $Token = Read-Host "Enter GitHub Personal Access Token"
}

$inputName = Read-Host "Enter runner name (press Enter for default)"
if (-not [string]::IsNullOrEmpty($inputName)) {
    $RunnerName = $inputName
}

# Download to current directory
Write-Step "Downloading GitHub Actions Runner v$RUNNER_VERSION"

$DownloadUrl = "https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/actions-runner-win-$ARCH-$RUNNER_VERSION.zip"
$ZipFile = "actions-runner-win-$ARCH-$RUNNER_VERSION.zip"
$ZipPath = Join-Path $CURRENT_DIR $ZipFile

Write-Host "Download location: $ZipPath" -ForegroundColor Yellow

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
    Write-Host "Removed old file"
}

try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath -ErrorAction Stop
    $fileSize = (Get-Item $ZipPath).Length / 1MB
    Write-Success "Downloaded runner ($([math]::Round($fileSize, 2)) MB)"
}
catch {
    Write-ErrorCustom "Failed to download runner: $_"
    exit 1
}

# Create runner directory
Write-Step "Creating runner directory"

if (-not (Test-Path $RUNNER_DIR)) {
    New-Item -ItemType Directory -Path $RUNNER_DIR -Force | Out-Null
    Write-Success "Created $RUNNER_DIR"
}
else {
    Write-Success "Directory already exists"
}

# Extract from current directory to runner directory
Write-Step "Extracting runner files from $ZipPath to $RUNNER_DIR"

try {
    # Use tar to extract
    tar -xf $ZipPath -C $RUNNER_DIR
    Write-Success "Runner extracted successfully"
}
catch {
    Write-Host "TAR extraction failed, trying Expand-Archive..."
    try {
        Expand-Archive -Path $ZipPath -DestinationPath $RUNNER_DIR -Force
        Write-Success "Runner extracted with Expand-Archive"
    }
    catch {
        Write-ErrorCustom "Failed to extract runner: $_"
        exit 1
    }
}

# Change to runner directory for configuration
Set-Location $RUNNER_DIR

Write-Step "Configuring the runner"
Write-Host "Connecting to: $RepoUrl"
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

Write-Step "Installing as Windows Service"

try {
    & .\svc.cmd install
    Write-Success "Service installed"
}
catch {
    Write-ErrorCustom "Failed to install service"
    exit 1
}

Write-Step "Starting service"

try {
    & .\svc.cmd start
    Write-Success "Service started"
}
catch {
    Write-ErrorCustom "Failed to start service"
    exit 1
}

Write-Step "Checking service status"
& .\svc.cmd status

Write-Host ""
Write-Success "GitHub Actions Runner Setup Complete!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Go to Settings → Actions → Runners in your GitHub repo"
Write-Host "2. Verify your runner shows as Online"
Write-Host "3. The runner will automatically pick up deployment jobs"
Write-Host ""
