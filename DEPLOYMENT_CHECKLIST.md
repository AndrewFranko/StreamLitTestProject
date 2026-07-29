# FactoryOps AI - Local Deployment Checklist

**Deployment Date:** 2026-07-28  
**Version:** 1.0 (MVP)  
**Environment:** Development

---

## Pre-Deployment Verification

### 1. File Structure
- [OK] `.env` - Environment configuration with GOOGLE_API_KEY
- [OK] `requirements.txt` - Python dependencies (7 packages)
- [OK] `src/agent.py` - Agent module with tools and role-based prompts
- [OK] `src/ui/app.py` - Streamlit UI application
- [OK] `src/data/machines.json` - Machine inventory (5 machines)
- [OK] `src/data/error_codes.json` - Error code reference (3 codes)
- [OK] `src/data/technicians.json` - Technician availability (3 technicians)
- [OK] `run.bat` - Windows startup script
- [OK] `run.sh` - Unix/Mac startup script

### 2. Environment Configuration
- [OK] GOOGLE_API_KEY: configured in `.env` (not shown for security)
- [OK] APP_ENV: `development`
- [OK] Path resolution fixed in `src/ui/app.py`

### 3. Data Files
- [OK] machines.json: 5 machines (MX-101, MX-204, MX-310, MX-405, MX-502)
- [OK] error_codes.json: 3 error codes (E17, E23, E45)
- [OK] technicians.json: 3 technicians (John, Sarah, Mike)

### 4. Agent Roles & Tools
- [OK] Operator role - Quick answers, safety-focused
- [OK] Engineer role - Technical diagnostics
- [OK] Supervisor role - Operational oversight
- [OK] Manager role - Strategic insights
- [OK] Tool: check_machine_status
- [OK] Tool: lookup_error_code
- [OK] Tool: check_technician_availability
- [OK] Tool: create_maintenance_ticket

---

## Installation & Startup Instructions

### For Windows Users

#### Step 1: Open Command Prompt
```
1. Press Win + R
2. Type: cmd
3. Press Enter
```

#### Step 2: Navigate to Project
```
cd c:\StreamLit
```

#### Step 3: Run Startup Script
```
run.bat
```

The script will:
- Verify Python installation
- Install all dependencies from requirements.txt
- Start Streamlit on http://localhost:8501

#### Step 4: Open in Browser
- Navigate to `http://localhost:8501`
- You should see the FactoryOps AI chat interface

---

### For Unix/Linux/Mac Users

#### Step 1: Open Terminal
```
1. Open your terminal application
2. Navigate to the project directory:
   cd /path/to/StreamLit
```

#### Step 2: Make Script Executable
```
chmod +x run.sh
```

#### Step 3: Run Startup Script
```
./run.sh
```

The script will:
- Verify Python 3 installation
- Install all dependencies from requirements.txt
- Start Streamlit on http://localhost:8501

#### Step 4: Open in Browser
- Navigate to `http://localhost:8501`
- You should see the FactoryOps AI chat interface

---

## Test Scenarios

### Test Scenario 1: Operator Role - Error Code Lookup
**Role:** Operator  
**Query:** "What is error code E17?"  
**Expected Behavior:**
- Agent explains E17 in simple, non-technical language
- Provides: Hydraulic pressure low, recommended action
- Suggests escalation to maintenance if needed

**Success Criteria:**
- Response uses tool: `lookup_error_code`
- Plain language explanation given
- Next steps clearly stated

---

### Test Scenario 2: Engineer Role - Machine Diagnostic
**Role:** Engineer  
**Query:** "Check machine MX-204"  
**Expected Behavior:**
- Agent retrieves machine status (currently in error state)
- Shows current error E17
- Provides technical diagnostic details
- Offers maintenance recommendations with part numbers

**Success Criteria:**
- Response uses tool: `check_machine_status`
- Technical depth appropriate for engineer
- Diagnostic procedure outlined
- Parts list provided if applicable

---

### Test Scenario 3: Supervisor Role - Shift Coordination
**Role:** Supervisor  
**Query:** "Create maintenance ticket for machine MX-204 with high priority"  
**Expected Behavior:**
- Agent recognizes critical action request
- Confirms action details
- Creates approval prompt (human-in-the-loop)
- Requires explicit approval before ticket creation
- Returns ticket ID upon approval

**Success Criteria:**
- Approval workflow triggered
- Ticket ID generated (TKT-YYYYMMDDHHMMSS format)
- User can approve or cancel action
- Chat history reflects approval status

---

### Test Scenario 4: Manager Role - Plant Summary
**Role:** Manager  
**Query:** "What is the current plant status?"  
**Expected Behavior:**
- Agent provides high-level operational overview
- Reports machines by status (running/idle/error/maintenance)
- Identifies critical issues requiring attention
- Suggests strategic recommendations

**Success Criteria:**
- Response includes multiple machine statuses
- Business impact analysis provided
- Executive-level language used
- Actionable recommendations included

---

### Test Scenario 5: Technician Availability Check
**Role:** Any  
**Query:** "Are technicians available for maintenance?"  
**Expected Behavior:**
- Agent queries technician database
- Lists available technicians with specialties
- Shows workload/current tasks
- Recommends best technician for issue type

**Success Criteria:**
- Response uses tool: `check_technician_availability`
- Lists 2 available technicians (John, Sarah)
- Shows Mike as busy (3 tasks)
- Recommends specialist match when relevant

---

### Test Scenario 6: Role Switching
**Action:** Change role from Operator to Engineer via sidebar  
**Expected Behavior:**
- Chat history clears
- Agent regenerates with new role prompt
- Sidebar shows updated role: "Engineer"
- Subsequent responses use engineer-specific language

**Success Criteria:**
- Role selector responsive
- Agent behavior changes based on role
- Conversation memory resets on role change
- All roles function independently

---

## Troubleshooting Guide

### Issue: "ModuleNotFoundError: No module named 'langchain'"
**Solution:**
1. Ensure dependencies installed: `pip install -r requirements.txt`
2. Verify Python version 3.10+: `python --version`
3. Check pip is for correct Python: `pip --version`

### Issue: "GOOGLE_API_KEY not set"
**Solution:**
1. Verify .env file exists: `cat .env` (Linux/Mac) or `type .env` (Windows)
2. Check key value is set (compare with .env.example format)
3. Restart Streamlit after fixing .env

### Issue: "FileNotFoundError: machines.json not found"
**Solution:**
1. Verify data files exist in `src/data/`
2. Check file permissions (should be readable)
3. Verify JSON formatting is valid: `python -m json.tool src/data/machines.json`

### Issue: Streamlit not responding or slow responses
**Solution:**
1. Check internet connection (Gemini API calls require connectivity)
2. Verify GOOGLE_API_KEY quota not exceeded
3. Clear browser cache and hard refresh (Ctrl+Shift+R)
4. Restart Streamlit server

### Issue: Port 8501 already in use
**Solution:**
```
# Find process using port 8501 and kill it
netstat -ano | findstr :8501  (Windows)
lsof -i :8501  (Mac/Linux)

# Or run on different port:
streamlit run src/ui/app.py --server.port 8502
```

---

## Performance Baselines

| Metric | Target | Notes |
|--------|--------|-------|
| Chat Response Latency | <5 seconds | Depends on Gemini API |
| Tool Execution | <500ms | JSON file lookups |
| Page Load | <2 seconds | Initial Streamlit load |
| Session Memory | <50MB | Per user session |

---

## Security Notes

1. **API Key Protection**
   - .env file is gitignored - never commit secrets
   - Rotate GOOGLE_API_KEY periodically
   - Monitor usage for anomalies

2. **Data Privacy**
   - Mock data only (no real production information)
   - Chat history stored in session memory only
   - No persistence to disk

3. **Input Validation**
   - Agent includes guardrails against prompt injection
   - Machine IDs validated against machines.json
   - Error codes validated against error_codes.json

---

## Next Steps

1. **Test all scenarios** outlined above
2. **Verify agent responses** for role-specific behavior
3. **Check error handling** when tool calls fail
4. **Monitor Gemini API usage** to stay within quota
5. **Plan Level 2 enhancement**: Multi-agent workflows

---

## Support & Debugging

**Log Location:** Streamlit logs appear in terminal where `run.bat/run.sh` was executed

**Enable Verbose Output:**
```
streamlit run src/ui/app.py --logger.level=debug
```

**API Usage Status:**
- Check Gemini API quota: https://console.cloud.google.com/
- Monitor spend and set alerts

**Common Queries for Testing:**
- "What is error E17?" (Error lookup)
- "Check machine MX-204" (Machine status)
- "Are technicians available?" (Resource check)
- "Create ticket for MX-310" (Ticket creation)

---

**Deployment Status:** READY FOR TESTING  
**Last Updated:** 2026-07-28  
**Next Review:** After initial testing phase
