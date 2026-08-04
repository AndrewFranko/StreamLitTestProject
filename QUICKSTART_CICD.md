# CI/CD Quick Start Guide

## 5-Minute Setup

### Prerequisites
- GitHub repository (already done ✓)
- Python 3.10+ on deployment target
- Git on deployment target

### Step 1: Copy Setup Script to Deployment Machine

**Linux/macOS:**
```bash
# Download the setup script
curl -O https://raw.githubusercontent.com/AndrewFranko/StreamLitTestProject/main/setup-runner.sh

# Run it
bash setup-runner.sh
```

**Windows (PowerShell as Admin):**
```powershell
# Download the setup script
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/AndrewFranko/StreamLitTestProject/main/setup-runner.ps1" -OutFile "setup-runner.ps1"

# Run it
.\setup-runner.ps1
```

### Step 2: During Setup, Provide:

1. **GitHub Repository URL**
   ```
   https://github.com/AndrewFranko/StreamLitTestProject
   ```

2. **Personal Access Token** (PAT)
   - Go to: https://github.com/settings/tokens/new
   - Create token with `repo` and `admin:org_hook` scopes
   - Copy and paste during setup

3. **Runner Name** (optional)
   - Default: `streamlit-deployment-runner`

### Step 3: Verify in GitHub

1. Go to: https://github.com/AndrewFranko/StreamLitTestProject/settings/actions/runners
2. Look for your runner with status **"Online"** (green dot)

### Step 4: Trigger Pipeline

```bash
# Make a change and push
cd StreamLitTestProject
git add .
git commit -m "Trigger CI/CD"
git push origin main
```

### Step 5: Watch It Run

Go to: https://github.com/AndrewFranko/StreamLitTestProject/actions

You'll see:
- ✓ **Build** job running...
- ✓ **Test** job running (after Build)...
- ✓ **Deploy** job running (after Test)...
- ✓ Application running on port 8501

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Runner shows "Offline" | Run setup script again, or restart: `sudo systemctl restart github-runner` |
| Build fails | Check Python version: `python --version` (need 3.10+) |
| Test fails | Review linting errors in GitHub Actions logs |
| Deploy fails | Check port 8501: `lsof -i :8501` or `netstat -ano \| findstr :8501` |
| App not accessible | Run: `bash verify-deployment.sh` |

---

## What Happens Automatically

```
Push to main
    ↓
Build (2-3 min)
    ├─ Python 3.10 setup
    ├─ pip install -r requirements.txt
    ├─ Syntax validation
    └─ Create artifacts
    ↓
Test (2-3 min)
    ├─ Download artifacts
    ├─ Lint code (flake8)
    ├─ Check formatting (black)
    ├─ Run tests (pytest)
    └─ Validate imports
    ↓
Deploy (2-3 min)
    ├─ Download artifacts
    ├─ Install on target
    ├─ Stop old instance
    ├─ Start new instance
    └─ Health check
    ↓
Done! App running on :8501
```

**Total time: 7-9 minutes**

---

## Monitor Status

### GitHub Web UI
- Actions tab shows real-time progress
- Click job to see detailed logs
- Green checkmark = success
- Red X = failure

### Command Line
```bash
# View runner logs (Linux)
sudo journalctl -u github-runner -f

# View runner logs (Windows)
Get-EventLog -LogName Application -Source GitHubActions -Newest 20

# Check app is running
curl http://localhost:8501
```

### Deployment Verification
```bash
# Full health check
bash verify-deployment.sh

# Quick check
ps aux | grep streamlit
```

---

## Common Tasks

### Re-run Failed Pipeline
1. Go to Actions tab
2. Find the failed run
3. Click "Re-run failed jobs"

### Stop the Application
```bash
# Linux/macOS
pkill -f "streamlit run"

# Windows
taskkill /F /IM python.exe
```

### View Application Logs
```bash
# Real-time logs
tail -f logs/app.log

# Last 50 lines
tail -50 logs/app.log
```

### Debug Why Deploy Failed
1. Go to Actions → Deploy job logs
2. Look for error messages
3. Check `.github/workflows/deploy.yml` for the issue
4. Fix code or configuration
5. Push again to retry

---

## Access the Application

After deployment succeeds:

- **Local Machine**: http://localhost:8501
- **Remote Machine**: http://<machine-ip>:8501
- **Custom Domain**: Configure reverse proxy (nginx, Apache)

---

## Next Steps

1. ✅ Setup runner (you're here)
2. ✅ Verify runner is online
3. Push code to trigger first pipeline
4. ✅ Monitor execution
5. ✅ Access running application

---

## Getting Help

- **Setup issues**: See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)
- **Detailed info**: See [CICD_IMPLEMENTATION_SUMMARY.md](CICD_IMPLEMENTATION_SUMMARY.md)
- **GitHub Actions docs**: https://docs.github.com/en/actions
- **Self-hosted runner docs**: https://docs.github.com/en/actions/hosting-your-own-runners

---

**Last Updated**: August 4, 2026
**Status**: Production Ready
