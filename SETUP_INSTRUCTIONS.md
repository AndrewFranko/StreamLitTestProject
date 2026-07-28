# FactoryOps AI Level 2 - Complete Setup Instructions

Comprehensive guide for setting up FactoryOps AI with tool calling capabilities.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Getting Gemini API Key](#getting-gemini-api-key)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Verification Checklist](#verification-checklist)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Required

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Internet**: Stable connection for API calls
- **RAM**: 4 GB minimum (8 GB recommended)
- **Storage**: 500 MB for dependencies

### Recommended

- **Virtual Environment Manager**: venv (included with Python)
- **Code Editor**: VS Code, PyCharm, or similar
- **Terminal/Shell**: bash (macOS/Linux) or PowerShell/cmd (Windows)

### Check Python Installation

```bash
python --version
```

If Python 3.10+ is installed, you'll see:
```
Python 3.10.x (or higher)
```

If not installed or outdated:
- **Windows**: Download from https://www.python.org/downloads/
- **macOS**: `brew install python@3.10` (requires Homebrew)
- **Linux**: `sudo apt install python3.10` (Ubuntu/Debian)

---

## Getting Gemini API Key

### Step 1: Go to Google AI Studio

1. Open https://makersuite.google.com/app/apikey
2. Sign in with your Google account (create one if needed)

### Step 2: Create API Key

1. Click **"Create API key"** button
2. Select **"Create API key in new project"**
3. Copy the generated key (it starts with `AIza...`)

### Step 3: Store Securely

- Keep this key **private** and **confidential**
- Never commit it to version control
- Never share it publicly
- Store in `.env` file (which is gitignored)

### Verify API Key Access

```bash
# After adding to .env, verify it's loaded
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key loaded:', bool(os.getenv('GOOGLE_API_KEY')))"
```

Expected output: `API Key loaded: True`

---

## Installation Steps

### Step 1: Clone or Download Repository

#### Option A: Clone with Git
```bash
git clone <repository-url>
cd factoryops-ai
```

#### Option B: Download ZIP
1. Click "Code" → "Download ZIP"
2. Extract the ZIP file
3. Open terminal in extracted directory

### Step 2: Create Virtual Environment

A virtual environment isolates project dependencies from system Python.

```bash
# Create venv
python -m venv venv

# Activate venv
# On macOS/Linux:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

**Verify activation**: Command prompt should show `(venv)` prefix

```bash
(venv) $ 
```

### Step 3: Upgrade pip (Recommended)

```bash
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
# Install exact versions specified in requirements.txt
pip install -r requirements.txt
```

**Expected output**: Shows installation progress, ending with `Successfully installed ...`

### Step 5: Verify Installation

```bash
# List installed packages
pip list

# Check LangChain installation
python -c "import langchain; print(f'LangChain {langchain.__version__} installed')"

# Check Streamlit installation
python -c "import streamlit; print(f'Streamlit {streamlit.__version__} installed')"

# Check Gemini integration
python -c "import langchain_google_genai; print('Gemini integration ready')"
```

All should succeed without errors.

---

## Configuration

### Step 1: Create .env File

```bash
# Copy template
cp .env.example .env
```

### Step 2: Add Your Gemini API Key

Edit `.env` file and add your key:

```ini
# .env
GOOGLE_API_KEY=AIza...your_actual_key...

# Optional settings (defaults shown)
APP_ENV=development
APP_NAME=FactoryOps AI
LOG_LEVEL=INFO
SESSION_TIMEOUT_MINUTES=30
MAX_CONVERSATION_LENGTH=100
```

### Step 3: Verify Configuration

```bash
# Test that .env loads correctly
python -c "from src.config import settings; print(f'Config loaded: {settings.app_name}')"
```

Expected output: `Config loaded: FactoryOps AI`

### File Permissions (macOS/Linux)

```bash
# Make .env readable by user only
chmod 600 .env
```

---

## Running the Application

### Start the Application

```bash
# Make sure venv is activated (you should see (venv) in prompt)
streamlit run src/ui/streamlit_app.py
```

### Expected Output

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501

  For better performance, install pyarrow: pip install --upgrade pyarrow
```

### Open in Browser

1. Open your web browser
2. Go to `http://localhost:8501`
3. You should see the FactoryOps AI chat interface

### Stop the Application

Press `Ctrl+C` in the terminal to stop

---

## Verification Checklist

Test these features to verify everything works:

### Test 1: Chat Interface Loads
- [ ] Browser opens to http://localhost:8501
- [ ] Chat input box is visible
- [ ] Role selector (Operator/Engineer/Supervisor/Manager) works

### Test 2: Role Selection
- [ ] Click "Engineer" in sidebar
- [ ] Role changes and interface updates
- [ ] System prompt changes (check in debug panel if enabled)

### Test 3: Simple Chat (No Tools)
- [ ] Type: "Hello, what can you help with?"
- [ ] Response appears in 2-3 seconds
- [ ] Response is role-appropriate (technical for Engineer, etc.)

### Test 4: Machine Status Tool
- [ ] Type: "Check the status of machine MX-204"
- [ ] Agent calls `check_machine_status` tool
- [ ] Returns machine status from `data/machines.json`
- [ ] Response synthesizes machine info into natural language

### Test 5: Error Code Lookup Tool
- [ ] Type: "What does error E17 mean?"
- [ ] Agent calls `lookup_error_code` tool
- [ ] Returns error explanation from `data/error_codes.json`
- [ ] Includes severity and recommended action

### Test 6: Create Ticket (Approval)
- [ ] Type: "Create maintenance ticket for MX-204 - pump failure"
- [ ] Agent drafts ticket details
- [ ] Shows confirmation message: "Approve ticket creation?"
- [ ] Click "Approve" → Ticket created with ID
- [ ] Click "Reject" → Ticket discarded

### Test 7: Technician Availability
- [ ] Type: "Who's available for electrical work?"
- [ ] Agent calls `check_technician_availability` tool
- [ ] Returns technician list from `data/technicians.json`

### Test 8: Multi-Tool Scenario
- [ ] Type: "Machine MX-204 has error E17. Diagnose."
- [ ] Agent invokes 2+ tools:
  - `lookup_error_code("E17")`
  - `check_machine_status("MX-204")`
- [ ] Synthesizes multi-tool info into diagnosis

---

## Project Structure

After installation, your directory should look like:

```
factoryops-ai/
├── .env                    # Your local secrets (don't commit)
├── .env.example            # Template (commit to git)
├── requirements.txt        # Exact dependency versions
├── QUICKSTART.md          # 5-minute setup guide
├── SETUP_INSTRUCTIONS.md  # This file
├── README.md              # Project overview
├── CLAUDE.md              # Full architecture
│
├── src/
│   ├── __init__.py
│   ├── config.py                   # Load .env, settings
│   │
│   ├── level1_chatbot/
│   │   ├── chat_engine.py
│   │   └── prompts.py
│   │
│   ├── level2_agent/
│   │   ├── agent.py               # AgentExecutor setup
│   │   └── tools/
│   │       ├── machine_status.py
│   │       ├── error_lookup.py
│   │       ├── ticket_creation.py
│   │       └── technician_checker.py
│   │
│   ├── data/                       # Mock data for tools
│   │   ├── machines.json
│   │   ├── error_codes.json
│   │   └── technicians.json
│   │
│   └── ui/
│       └── streamlit_app.py
│
├── tests/
│   └── test_agent.py
│
└── data/                           # Runtime data
    ├── machines.json
    ├── error_codes.json
    └── technicians.json
```

---

## Troubleshooting

### Issue: Python not found

**Error**: `python: command not found` or `'python' is not recognized`

**Solution**:
- Python not installed - download from https://www.python.org
- On macOS/Linux, might need `python3` instead:
  ```bash
  python3 --version
  python3 -m venv venv
  source venv/bin/activate
  ```

### Issue: Virtual environment not activating

**Error**: `(venv)` doesn't appear in prompt

**Solution**:
```bash
# On Windows PowerShell, you might need to allow scripts:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate:
venv\Scripts\Activate.ps1
```

### Issue: Dependencies won't install

**Error**: `pip install -r requirements.txt` fails

**Solution**:
```bash
# Clear pip cache and reinstall
pip install -r requirements.txt --force-reinstall --no-cache-dir
```

### Issue: GOOGLE_API_KEY not found

**Error**: `GOOGLE_API_KEY environment variable not found`

**Solution**:
```bash
# Verify .env exists
ls -la .env

# Verify it has your key
grep GOOGLE_API_KEY .env

# Verify no typos in key
cat .env
```

### Issue: Gemini API returns 401 Unauthorized

**Error**: `Invalid API key` or `API_KEY_INVALID`

**Solution**:
1. Verify key is correct at https://makersuite.google.com/app/apikey
2. Regenerate if needed
3. Update `.env` with new key
4. Restart Streamlit app (`Ctrl+C`, then run again)

### Issue: "ModuleNotFoundError: langchain"

**Error**: Module import fails despite pip install

**Solution**:
```bash
# Ensure venv is activated (look for (venv) in prompt)
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Reinstall
pip install langchain==0.2.8 langchain-google-genai==0.1.3
```

### Issue: Streamlit port 8501 already in use

**Error**: `Streamlit is already running on port 8501`

**Solution**:
```bash
# Run on different port
streamlit run src/ui/streamlit_app.py --server.port 8502
```

### Issue: Response takes >10 seconds

**Cause**: Slow network, API throttling, or model loading

**Solution**:
- First request is slower (model initialization) - wait up to 10s
- Check internet speed: `ping google.com`
- Check API quota: https://console.cloud.google.com/apis/dashboard
- Try clearing browser cache (`Ctrl+Shift+Delete`)

### Issue: Tool calls fail silently

**Error**: Agent doesn't invoke tools

**Debug**:
1. Enable debug mode in Streamlit sidebar
2. Check if `data/machines.json`, etc. exist
3. Verify data file JSON syntax
4. Check agent tool definitions in `src/level2_agent/agent.py`

---

## Next Steps After Setup

### 1. Test All Features (5 minutes)
Follow the "Verification Checklist" above

### 2. Customize for Your Plant (30 minutes)
- Edit `data/machines.json` - Add your machine IDs
- Edit `data/error_codes.json` - Add your error codes
- Edit `data/technicians.json` - Add your staff

### 3. Connect Real APIs (Optional, Level 2+)
- Replace mock tools with real API calls
- Update `src/level2_agent/tools/` files

### 4. Deploy to Production (See DEPLOYMENT_CHECKLIST.md)
- Docker containerization
- Database setup
- Authentication & authorization
- Monitoring & logging

---

## Support & Documentation

| Resource | Purpose |
|----------|---------|
| `QUICKSTART.md` | 5-minute setup guide |
| `README.md` | Project overview & features |
| `CLAUDE.md` | Full architecture & design |
| https://ai.google.dev | Gemini API documentation |
| https://docs.streamlit.io | Streamlit documentation |
| https://python.langchain.com | LangChain documentation |

---

## Configuration Reference

### .env File Options

```ini
# Required
GOOGLE_API_KEY=your_key_here

# Application (optional, defaults shown)
APP_ENV=development                    # development, staging, production
APP_NAME=FactoryOps AI                # Application display name
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR

# Session Management
SESSION_TIMEOUT_MINUTES=30            # Auto-logout after inactivity
MAX_CONVERSATION_LENGTH=100           # Max messages in memory

# Database (for Level 3+)
DATABASE_URL=sqlite:///./data/factory_ops.db

# API Integrations (for Level 2+)
MES_API_URL=http://mes-internal.factoryops.com/api
MAINTENANCE_API_URL=http://maintenance.factoryops.com/api
INVENTORY_API_URL=http://inventory.factoryops.com/api
```

---

**Version**: 2.0.0  
**Last Updated**: 2026-07-28  
**Status**: ✅ Ready for Production
