# Manual Test Example - Memory Isolation

**Goal**: Test that operator and engineer have completely separate memory

## Steps

### 1. Start the app
```bash
streamlit run app.py
```
Open: http://localhost:8501

### 2. Test role isolation in browser

**Operator role:**
- Sidebar: Select "Operator"
- New Chat
- Ask: "What is error code E17?"
- See response about hydraulic pressure

**Switch to Engineer:**
- Sidebar: Select "Engineer"
- Notice: Chat area shows "Select or create a chat" (operator's chat is gone)
- New Chat
- Ask: "How do I diagnose E17?"
- See technical response

**Switch back to Operator:**
- Sidebar: Select "Operator"
- ✅ Your original "What is error code E17?" chat reappears
- ✅ Engineer's chat is NOT visible

**Result**: ✅ Each role has completely separate chat history

---

### 3. Test memory isolation in Python

Run this script:

```bash
cd c:/StreamLit
python << 'EOF'
import sys
sys.path.insert(0, 'src')
from agent_engine import AgentEngine

# Create two agents
operator = AgentEngine('operator')
engineer = AgentEngine('engineer')

# Operator stores memory
operator.store_memory(
    key='machine_preference',
    value='MX-204 works best in early morning',
    tags=['machine', 'MX-204']
)
print("✓ Operator stored: machine_preference")

# Engineer tries to retrieve it
result = engineer.retrieve_memory('machine_preference')
if result is None:
    print("✓ Engineer cannot see operator's memory (ISOLATION WORKS)")
else:
    print("✗ Engineer retrieved operator's data (ISOLATION BROKEN)")

# Engineer stores memory
engineer.store_memory(
    key='diagnostic_note',
    value='E17 means low hydraulic pressure',
    tags=['E17', 'diagnostic']
)
print("✓ Engineer stored: diagnostic_note")

# Operator tries to retrieve it
result = operator.retrieve_memory('diagnostic_note')
if result is None:
    print("✓ Operator cannot see engineer's memory (ISOLATION WORKS)")
else:
    print("✗ Operator retrieved engineer's data (ISOLATION BROKEN)")
EOF
```

**Expected Output:**
```
✓ Operator stored: machine_preference
✓ Engineer cannot see operator's memory (ISOLATION WORKS)
✓ Engineer stored: diagnostic_note
✓ Operator cannot see engineer's memory (ISOLATION WORKS)
```

**Result**: ✅ Memory completely isolated per role
