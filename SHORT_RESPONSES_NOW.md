# Short Responses - Agent Prompts Updated

## What Changed

Updated system prompts to make agent responses **ultra-concise**:

### Engineer Agent (`src/agents/engineer_agent.py`):

**Old response style:**
- Technical but accessible
- Diagnostic steps, part numbers, time estimates
- Historical patterns referenced
- Confidence levels included

**New response style:**
```
Ultra-concise, direct answers (1-3 sentences max)
No lengthy explanations
Get to the point immediately
For normal Q&A: one sentence answer
```

### Ticket Creation Format:

**Old:**
```
"I'm ready to create this maintenance ticket.

Machine: MX-204
Priority: high
Description: Coolant pump is failing and needs replacement

Does this look correct? Please approve to proceed."
```

**New:**
```
"I'm ready to create this ticket.
Machine: MX-204
Priority: high
Description: Coolant pump

Approve?"
```

### Result:
- ~200 characters → ~50 characters
- Much faster to read
- Cleaner chat display
- Still contains all info needed

## Operator Agent Same Changes

Updated `src/agents/operator_agent.py` with similar short response requirements.

## Examples of New Responses

### Machine Status Check
**Request:** "What's the status of MX-204?"
**Old response:** "Machine MX-204 is currently running with error E17 (coolant pressure low). The machine has 94.2% uptime over the last 7 days..."
**New response:** "MX-204 running. Error E17 (coolant pressure low)."

### Error Code Lookup
**Request:** "What does error E17 mean?"
**Old response:** "Error E17: Coolant System Pressure Failure. What it means: The cooling system pressure has dropped below safe operating level. Severity: MEDIUM..."
**New response:** "E17: Coolant pressure low. Refill or check leaks."

### Ticket Creation
**Request:** "Create ticket for MX-204, coolant pump broken, high priority"
**Old response:** "I'm ready to create this maintenance ticket. Machine: MX-204..."
**New response:** "I'm ready to create this ticket. Machine: MX-204 Priority: high Description: Coolant pump Approve?"

## Benefits

✅ Much less text to read  
✅ Faster to scan messages  
✅ Cleaner chat display  
✅ Same information, condensed  
✅ Better mobile experience  
✅ Easier to find approval buttons  

## Test It

```bash
streamlit run src/ui/streamlit_app.py
```

Log in and try:
- "What's the status of MX-204?" → One short line response
- "What does error E17 mean?" → Concise answer
- "Create ticket for MX-204, coolant pump, high priority" → Short approval request

Responses now appear in chat as single short lines or 2-3 short sentences.

---

**Status**: Agent responses now ultra-concise! ✅
