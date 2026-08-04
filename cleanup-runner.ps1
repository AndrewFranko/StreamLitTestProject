# GitHub Actions Runner Cleanup Script
# Run as Administrator - Cleans up corrupted runner installation

# Check if running as Administrator
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "FAIL This script must be run as Administrator!" -ForegroundColor Red
    exit 1
}

Write-Host "GitHub Actions Runner Cleanup"
Write-Host ""

$RUNNER_DIR = "$env:USERPROFILE\github-runner"

# Stop the runner service if it's running
Write-Host "==> Stopping runner service (if running)"
try {
    net stop GitHubRunner
    Write-Host "PASS Service stopped" -ForegroundColor Green
}
catch {
    Write-Host "INFO Service not running (OK)" -ForegroundColor Cyan
}

# Wait a moment for service to stop
Start-Sleep -Seconds 2

# Delete the corrupted ZIP file
Write-Host "==> Deleting corrupted ZIP file"
$ZipPath = "$RUNNER_DIR\actions-runner-win-x64-2.319.0.zip"
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
    Write-Host "PASS Deleted corrupted ZIP" -ForegroundColor Green
}
else {
    Write-Host "INFO ZIP file not found (OK)" -ForegroundColor Cyan
}

# Delete extracted files to force fresh extraction
Write-Host "==> Deleting extracted runner files"
$filesToDelete = @(
    "$RUNNER_DIR\bin",
    "$RUNNER_DIR\externals",
    "$RUNNER_DIR\*.exe",
    "$RUNNER_DIR\*.dll",
    "$RUNNER_DIR\*.json"
)

foreach ($pattern in $filesToDelete) {
    Get-Item $pattern -ErrorAction SilentlyContinue | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
}

Write-Host "PASS Cleaned up extracted files" -ForegroundColor Green

# List what's left
Write-Host ""
Write-Host "==> Runner directory contents after cleanup:"
if (Test-Path $RUNNER_DIR) {
    Get-ChildItem $RUNNER_DIR
}

Write-Host ""
Write-Host "PASS Cleanup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Run setup-runner.ps1 to reinstall"
Write-Host ""
