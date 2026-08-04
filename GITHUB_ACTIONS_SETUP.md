# GitHub Actions CI/CD Pipeline Setup Guide

This guide walks you through setting up the GitHub Actions CI/CD pipeline for the StreamLitTestProject (FactoryOps AI).

## Overview

The CI/CD pipeline has three main jobs:

1. **Build** (GitHub Hosted Runner)
   - Checks out the code
   - Sets up Python 3.10
   - Installs dependencies
   - Verifies Python syntax
   - Creates build artifacts

2. **Test** (GitHub Hosted Runner)
   - Downloads build artifacts
   - Runs linting with flake8
   - Checks code formatting with black
   - Validates import ordering with isort
   - Runs unit tests with pytest
   - Tests module imports

3. **Deploy** (Self-Hosted Runner)
   - Downloads build artifacts
   - Installs dependencies on the target machine
   - Stops any previous instances
   - Deploys the Streamlit application
   - Verifies the deployment
   - Sends deployment notifications

## Prerequisites

- GitHub account with administrative access to the repository
- Target machine (local, VM, or cloud instance) to deploy the application
- Python 3.10+ installed on the target machine
- Git installed on both local development machine and target machine

## Step 1: Push Your Code to GitHub

First, ensure all your code is committed and pushed to the GitHub repository:

```bash
cd StreamLitTestProject
git status
git add .
git commit -m "Add GitHub Actions CI/CD pipeline"
git push origin main
```

## Step 2: Configure Self-Hosted Runner

### On Your Target Machine (Deployment Server)

#### 2.1 Create a dedicated directory for the runner

```bash
# Create a directory for GitHub Actions runner
mkdir -p ~/github-runner
cd ~/github-runner
```

#### 2.2 Download the GitHub Actions Runner

```bash
# For Linux/macOS:
curl -o actions-runner-linux-x64-2.319.0.tar.gz \
  -L https://github.com/actions/runner/releases/download/v2.319.0/actions-runner-linux-x64-2.319.0.tar.gz

tar xzf actions-runner-linux-x64-2.319.0.tar.gz

# For Windows (PowerShell):
# Visit https://github.com/actions/runner/releases
# Download the latest windows-x64 release and extract it
```

#### 2.3 Generate a Personal Access Token (PAT)

1. Go to GitHub: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: `CI_CD_RUNNER_TOKEN`
4. Select scopes:
   - `repo` (full control of private repositories)
   - `admin:org_hook` (access to webhooks)
5. Copy the token (you'll need it next)

#### 2.4 Configure the Runner

```bash
cd ~/github-runner

# Replace:
# <TOKEN> with your PAT from step 2.3
# <REPO_URL> with your GitHub repo URL (e.g., https://github.com/username/repo)
# <RUNNER_NAME> with a descriptive name (e.g., "deployment-server")

./config.sh --url <REPO_URL> --token <TOKEN> --name <RUNNER_NAME> --labels linux,streamlit,deployment
```

Example:
```bash
./config.sh --url https://github.com/AndrewFranko/StreamLitTestProject \
  --token ghp_xxxxxxxxxxxxxxxxxxxx \
  --name deployment-server \
  --labels linux,streamlit,deployment
```

#### 2.5 Run the Runner as a Service (Recommended for Production)

**Option A: systemd (Linux)**

```bash
# Create systemd service file
sudo nano /etc/systemd/system/github-runner.service
```

Paste the following content:

```ini
[Unit]
Description=GitHub Actions Runner
After=network.target

[Service]
Type=simple
User=<YOUR_USERNAME>
WorkingDirectory=/home/<YOUR_USERNAME>/github-runner
ExecStart=/home/<YOUR_USERNAME>/github-runner/run.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable github-runner
sudo systemctl start github-runner
sudo systemctl status github-runner
```

**Option B: nohup (Quick Start - Linux/macOS)**

```bash
cd ~/github-runner
nohup ./run.sh > runner.log 2>&1 &
```

**Option C: Task Scheduler (Windows)**

Run PowerShell as Administrator:

```powershell
# Navigate to runner directory
cd C:\github-runner

# Run the configuration
.\config.cmd --url <REPO_URL> --token <TOKEN> --name <RUNNER_NAME>

# Install as service
.\svc.cmd install

# Start the service
.\svc.cmd start

# Check status
.\svc.cmd status
```

## Step 3: Verify Self-Hosted Runner Setup

### On GitHub

1. Go to your repository: https://github.com/AndrewFranko/StreamLitTestProject
2. Navigate to **Settings** → **Actions** → **Runners**
3. You should see your runner listed with status "Online" (green dot)

### On Your Target Machine

```bash
# Check if the runner is listening for jobs
tail -f ~/github-runner/_diag/Runner_* 2>/dev/null

# Or check via systemd
sudo journalctl -u github-runner -f
```

## Step 4: Trigger the CI/CD Pipeline

### Option A: Push to Main Branch

```bash
cd StreamLitTestProject
# Make a small change (already done)
git add .
git commit -m "Trigger CI/CD pipeline"
git push origin main
```

### Option B: Manual Trigger (if using workflow_dispatch)

In GitHub web interface:
1. Go to **Actions** tab
2. Select the **CI/CD Pipeline** workflow
3. Click "Run workflow"
4. Select the branch and click "Run workflow"

## Step 5: Monitor Pipeline Execution

### View Pipeline Status

1. Go to your repository on GitHub
2. Click the **Actions** tab
3. You'll see the workflow run with three jobs:
   - ✓ **Build** (runs on GitHub-hosted runner)
   - ✓ **Test** (runs on GitHub-hosted runner, depends on Build)
   - ✓ **Deploy** (runs on self-hosted runner, depends on Test)

### Real-Time Logs

Click on each job to see detailed logs of the build, test, and deploy steps.

### View Artifacts

After Build completes, you can download artifacts:
- Click the workflow run
- Scroll to "Artifacts"
- Download `build-artifacts` and `test-reports`

## Step 6: Verify Deployment

After the Deploy job completes successfully:

1. **Check the application is running:**
   ```bash
   curl http://localhost:8501
   ```

2. **View application logs:**
   ```bash
   tail -f ~/github-runner/_work/StreamLitTestProject/StreamLitTestProject/logs/app.log
   ```

3. **Open in browser:**
   - Local: http://localhost:8501
   - Remote: http://<target-machine-ip>:8501

## Troubleshooting

### Runner Shows "Offline" Status

```bash
# Check if the runner process is running
ps aux | grep run.sh

# Restart the runner
sudo systemctl restart github-runner

# Or if using nohup
pkill -f run.sh
cd ~/github-runner && nohup ./run.sh > runner.log 2>&1 &
```

### Build Fails: Dependencies Not Found

The GitHub-hosted runner uses `actions/setup-python@v4` with pip caching. Ensure your `requirements.txt` is valid:

```bash
# Test locally
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
```

### Deploy Fails: Port Already in Use

The pipeline automatically kills previous instances. If it still fails:

```bash
# Find and kill the process
lsof -i :8501
kill -9 <PID>

# Or for Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### Deploy Fails: Application Not Starting

Check the application logs:

```bash
cat ~/github-runner/_work/StreamLitTestProject/StreamLitTestProject/logs/app.log
```

Common issues:
- Missing `.env` file or environment variables
- Port 8501 already in use
- Missing Python dependencies

## Advanced Configuration

### Add Manual Approval for Deployment

Edit `.github/workflows/deploy.yml` to add environment protection:

```yaml
deploy:
  name: Deploy
  needs: test
  environment: production  # Add this
  runs-on: self-hosted
```

Then in GitHub:
1. Go to **Settings** → **Environments** → **production**
2. Add required reviewers
3. Now deployments require manual approval

### Add Slack/Email Notifications

Install a notification action:

```yaml
- name: Send Slack notification
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Deployment completed: ${{ job.status }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "FactoryOps AI Deployment\nStatus: *${{ job.status }}*\nBranch: *${{ github.ref }}*\nCommit: `${{ github.sha }}`"
            }
          }
        ]
      }
```

### Upload Build Artifacts to S3 (Optional)

```yaml
- name: Upload to S3
  uses: aws-actions/configure-aws-credentials@v2
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: us-east-1

- name: Push artifacts to S3
  run: |
    aws s3 cp requirements.txt s3://my-bucket/builds/${{ github.sha }}/
```

## Maintenance

### Update Runner Regularly

Check for updates:
```bash
cd ~/github-runner
./config.sh --check
```

To update:
```bash
# Stop the runner
sudo systemctl stop github-runner

# Download new version and extract
# Then restart
sudo systemctl start github-runner
```

### Monitor Runner Health

```bash
# View runner diagnostic logs
tail -f ~/github-runner/_diag/Runner_*

# View systemd logs
sudo journalctl -u github-runner -f --since "10 minutes ago"
```

## Next Steps

1. **Add Status Badge to README:**
   ```markdown
   [![CI/CD Pipeline](https://github.com/AndrewFranko/StreamLitTestProject/actions/workflows/deploy.yml/badge.svg)](https://github.com/AndrewFranko/StreamLitTestProject/actions)
   ```

2. **Set up notifications** for pipeline failures

3. **Configure environment protection** for production deployments

4. **Document deployment procedures** for your team

5. **Monitor application performance** after deployment

## Support

For issues or questions:
- Check the GitHub Actions logs in the web interface
- Review the runner diagnostic logs on your target machine
- Consult the [GitHub Actions Documentation](https://docs.github.com/en/actions)
- Check the [GitHub Runner Documentation](https://docs.github.com/en/actions/hosting-your-own-runners)
