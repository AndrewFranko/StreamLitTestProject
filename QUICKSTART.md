# FactoryOps AI Level 2 - Quick Start Guide (5 Steps)

Get FactoryOps AI running in 5 minutes with tool calling capability.

---

## Step 1: Prerequisites

Before starting, ensure you have:

- **Python 3.10+** installed
- **Google Gemini API Key** - [Get one free](https://makersuite.google.com/app/apikey)
- **Git** (optional, for version control)

### Check Python Version

```bash
python --version
# Expected output: Python 3.10.x or higher
```

---

## Step 2: Clone & Setup Environment

```bash
# Navigate to project directory
cd factoryops-ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

**Expected output**: Command prompt shows `(venv)` prefix

---

## Step 3: Install Dependencies

```bash
# Install exact versions for 2026
pip install -r requirements.txt
```

**Expected output**: 
```
Successfully installed langchain-0.2.8
Successfully installed google-generativeai-0.5.4
Successfully installed streamlit-1.35.0
...
```

---

## Step 4: Configure API Key

```bash
# Copy configuration template
cp .env.example .env

# Edit .env and add your Gemini API key
# macOS/Linux:
nano .env

# Windows:
notepad .env
```

**What to add**:
```ini
GOOGLE_API_KEY=your_actual_gemini_key_here
```

**Save and close the file.**

### Verify Configuration

```bash
# Check .env exists and has content
cat .env | grep GOOGLE_API_KEY
```

Expected: `GOOGLE_API_KEY=...your_key...`

---

## Step 5: Run the Application

```bash
streamlit run src/ui/streamlit_app.py
```

**Expected output**:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Open your browser to `http://localhost:8501`

---

## Test the Agent

Once the app is running, test these scenarios:

### Test 1: Ask About a Machine
1. Select **Engineer** role
2. Ask: "What is the status of machine MX-204?"
3. **Expected**: Agent calls `check_machine_status` and returns machine details

### Test 2: Look Up Error Code
1. Keep **Engineer** role
2. Ask: "What does error E17 mean?"
3. **Expected**: Agent calls `lookup_error_code` and explains the error

### Test 3: Create Maintenance Ticket (with Approval)
1. Still in **Engineer** role
2. Ask: "Create a maintenance ticket for MX-204 - pump seal replacement needed"
3. **Expected**: 
   - Agent prepares ticket details
   - Shows draft in UI
   - **Asks for your approval**
   - Creates ticket on confirmation

### Test 4: Check Technician Availability
1. Ask: "Who's available for hydraulic repairs?"
2. **Expected**: Agent returns list of available technicians with specialties

### Test 5: Multi-Step Diagnosis
1. Ask: "Machine MX-204 has error E17. What should I do?"
2. **Expected**: Agent performs multiple tool calls:
   - Looks up error code
   - Checks machine status
   - Synthesizes recommendation
   - Offers to create ticket

---

## Data Files

Mock data for testing is stored in `/c/StreamLit/data/`:

```
data/
├── machines.json       # Machine specifications and status
├── error_codes.json    # Error code meanings
└── technicians.json    # Available technicians and specialties
```

The agent reads from these files when you ask questions.

---

## Troubleshooting

### Error: `GOOGLE_API_KEY not found`
```bash
# Verify .env file exists
ls -la .env

# Verify it has your key
grep GOOGLE_API_KEY .env
```

### Error: `ModuleNotFoundError: langchain`
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Error: Streamlit connection timeout
- Check your internet connection
- Verify Gemini API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
- Check Gemini API quota in Google Cloud Console

### Slow responses (>10 seconds)
- Wait - first request is slower due to model loading
- Subsequent requests should be 2-5 seconds
- Check internet speed
- Try refreshing the browser

---

## What's Next?

### Customize for Your Plant

Edit the mock data files to match your machines:

1. **machines.json** - Update machine IDs (MX-101, etc.)
2. **error_codes.json** - Add your error codes (E01, E02, etc.)
3. **technicians.json** - Add your maintenance staff

### Deploy to Production

See full deployment instructions in `DEPLOYMENT_CHECKLIST.md`

### Connect to Real APIs

Replace mock tool functions with real API calls in `src/level2_agent/tools/`

---

## Performance Expectations

- **First request**: 3-5 seconds (model loading)
- **Subsequent requests**: 2-3 seconds (chat)
- **Tool invocations**: 1-2 seconds per tool
- **Memory per session**: < 50 MB

---

## Support

- **Architecture questions**: See `CLAUDE.md`
- **Detailed setup**: See `README.md`
- **Implementation details**: Check `src/` directory docstrings
- **Gemini API docs**: https://ai.google.dev

---

**Ready to deploy?** See `DEPLOYMENT_CHECKLIST.md` for production setup.

**Version**: 2.0.0  
**Last Updated**: 2026-07-28
