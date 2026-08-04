# StreamLitTestProject

A test project for exploring Streamlit and LangChain integration.

## CI/CD Pipeline Status

[![CI/CD Pipeline](https://github.com/AndrewFranko/StreamLitTestProject/actions/workflows/deploy.yml/badge.svg)](https://github.com/AndrewFranko/StreamLitTestProject/actions/workflows/deploy.yml)

## Overview

This project implements a comprehensive GitHub Actions CI/CD pipeline that automatically builds, tests, and deploys the FactoryOps AI manufacturing assistant.

### Pipeline Architecture

```
Developer Push
    ↓
GitHub Repository
    ↓
Build Job (GitHub Hosted)
    ├─ Checkout code
    ├─ Setup Python 3.10
    ├─ Install dependencies
    └─ Verify syntax & create artifacts
    ↓
Test Job (GitHub Hosted)
    ├─ Download build artifacts
    ├─ Run linting (flake8)
    ├─ Check formatting (black)
    ├─ Run tests (pytest)
    └─ Validate imports
    ↓
Deploy Job (Self-Hosted Runner)
    ├─ Download artifacts
    ├─ Install dependencies
    ├─ Stop previous instances
    ├─ Deploy application
    └─ Verify deployment
    ↓
Running Application (Port 8501)
```

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/AndrewFranko/StreamLitTestProject.git
cd StreamLitTestProject

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Setting Up CI/CD

See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for detailed instructions on:
- Configuring the self-hosted runner
- GitHub Actions workflow overview
- Troubleshooting common issues

## Features

### Automated Build Process
- Python syntax validation
- Dependency resolution
- Build artifact creation

### Automated Testing
- Code linting with flake8
- Code formatting checks with black
- Import order validation with isort
- Unit tests with pytest
- Module import verification

### Automated Deployment
- Application deployment to Streamlit
- Previous instance cleanup
- Deployment verification
- Health checks
- Automatic restart on failure

## Project Structure

```
StreamLitTestProject/
├── .github/
│   └── workflows/
│       ├── deploy.yml          # Main CI/CD pipeline
│       └── test-only.yml       # PR testing workflow
├── app.py                      # Main Streamlit app
├── pages/                      # Streamlit pages
├── src/                        # Source modules
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── GITHUB_ACTIONS_SETUP.md     # Setup guide
├── setup-runner.sh             # Linux/macOS runner setup
└── setup-runner.ps1            # Windows runner setup
```

## GitHub Actions Workflows

### Main Pipeline (`deploy.yml`)
- **Trigger**: Push to `main` or `develop` branches
- **Jobs**:
  1. Build (GitHub-hosted)
  2. Test (GitHub-hosted, depends on Build)
  3. Deploy (Self-hosted, depends on Test)
  4. Notify (Status notification)

### PR Testing (`test-only.yml`)
- **Trigger**: Pull requests to `main` or `develop`
- **Jobs**: Test only (no deployment)

## Viewing Pipeline Status

1. **GitHub Web Interface**
   - Go to [Actions](https://github.com/AndrewFranko/StreamLitTestProject/actions)
   - Click on a workflow run to see detailed logs

2. **Command Line**
   ```bash
   # Using GitHub CLI
   gh run list
   gh run view <RUN_ID>
   ```

3. **Status Badge**
   - Embed the badge in your README (already added above)
   - Links directly to the Actions page

## Deployment Verification

After successful deployment:

```bash
# Check if application is running
curl http://localhost:8501

# View application logs
tail -f logs/app.log

# Check process
ps aux | grep streamlit
```

## Environment Variables

Create a `.env` file with required configuration:

```ini
GOOGLE_API_KEY=your_key_here
# Add other environment variables as needed
```

The `.env` file should be created on the deployment target machine.

## Troubleshooting

### Runner is Offline
```bash
# Linux/macOS
sudo systemctl restart github-runner

# Windows
net stop github-runner && net start github-runner
```

### Build Fails
- Check Python version: `python --version` (should be 3.10+)
- Verify dependencies: `pip install -r requirements.txt`
- Review build logs in GitHub Actions

### Deploy Fails
- Check port availability: `lsof -i :8501`
- View deployment logs: `tail -f logs/app.log`
- Verify .env configuration on target machine

See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for more troubleshooting steps.

## Next Steps

1. ✅ Set up self-hosted runner
2. ✅ Push code to trigger pipeline
3. ✅ Monitor workflow execution
4. ⬜ Add environment protection (optional)
5. ⬜ Configure Slack notifications (optional)

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Self-Hosted Runners Guide](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FactoryOps AI Project Details](CLAUDE.md)

## License

See [LICENSE](LICENSE) for details.