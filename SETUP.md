# FactoryOps AI - Quick Setup Guide

## Deployment Summary

All files are ready for local deployment. No additional configuration needed.

## What's Included

✓ **Environment Config:** `.env` with GOOGLE_API_KEY configured  
✓ **Dependencies:** `requirements.txt` with all needed packages  
✓ **Agent Module:** `src/agent.py` with 4 roles and 4 tools  
✓ **UI App:** `src/ui/app.py` Streamlit interface  
✓ **Data Files:** Machines, error codes, technicians JSON  
✓ **Startup Scripts:** `run.bat` (Windows) and `run.sh` (Unix)  

## Quick Start

### Windows
```
cd c:\StreamLit
run.bat
```

### Unix/Mac
```
cd /path/to/StreamLit
chmod +x run.sh
./run.sh
```

Both scripts will:
1. Verify Python installation
2. Install dependencies
3. Start Streamlit on http://localhost:8501

## Verify Installation

After Streamlit starts, you should see:
```
  You can now view your Streamlit app in your browser.
  
  Local URL: http://localhost:8501
  Network URL: http://[YOUR_IP]:8501
```

Open http://localhost:8501 in your browser.

## Test It

In the Streamlit interface:

1. **Select a role** from sidebar (Operator, Engineer, Supervisor, Manager)
2. **Ask a question:**
   - Operator: "What is error E17?"
   - Engineer: "Check machine MX-204"
   - Supervisor: "Are technicians available?"
   - Manager: "What's the plant status?"
3. **Watch the agent respond** with role-specific answers

## Agent Capabilities

### Roles Available
- **Operator:** Machine procedures, error codes, safety
- **Engineer:** Technical diagnostics, maintenance procedures
- **Supervisor:** Real-time status, shift coordination
- **Manager:** Strategic KPIs, trends, recommendations

### Tools Available
- `check_machine_status` - Get machine state and errors
- `lookup_error_code` - Understand error codes
- `check_technician_availability` - Find available staff
- `create_maintenance_ticket` - Log maintenance issues

## Data Available

**Machines:** MX-101, MX-204, MX-310, MX-405, MX-502  
**Error Codes:** E17, E23, E45  
**Technicians:** John (hydraulic), Sarah (electrical), Mike (mechanical)  

## Troubleshooting

**Dependencies won't install?**
```
pip install --upgrade pip
pip install -r requirements.txt
```

**Python not found?**
- Install from https://www.python.org (Python 3.10+)
- Make sure to "Add Python to PATH" during installation

**Port 8501 already in use?**
```
streamlit run src/ui/app.py --server.port 8502
```

**API Key error?**
- Verify `.env` file has GOOGLE_API_KEY value
- Make sure no quotes around the key value

## Project Structure

```
c:\StreamLit\
├── .env                    # API keys (gitignored)
├── requirements.txt        # Python packages
├── run.bat                 # Windows startup
├── run.sh                  # Unix startup
├── DEPLOYMENT_CHECKLIST.md # Full verification
├── src/
│   ├── agent.py            # LangChain agent logic
│   ├── ui/
│   │   └── app.py          # Streamlit interface
│   └── data/
│       ├── machines.json
│       ├── error_codes.json
│       └── technicians.json
└── (chat history stored in session memory)
```

## Next Steps

1. Run the startup script
2. Open http://localhost:8501
3. Test each role with sample queries
4. Review responses for role-specific behavior
5. Check that tools are being invoked correctly

## Environment

- **OS:** Windows 11
- **Python:** 3.14 (installed locally)
- **API:** Google Gemini (gemini-1.5-pro)
- **Database:** JSON files (development)

## Notes

- All data is mock/test data
- Chat history is session-only (not persistent)
- Tickets created in session go to `src/data/tickets.json`
- API calls require active internet connection

---

**Status:** READY TO DEPLOY  
**Date:** 2026-07-28
