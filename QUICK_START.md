# FactoryOps AI - Quick Start Guide

## Prerequisites

- Python 3.10+ (tested on 3.13, 3.14)
- Google Gemini API key

## Installation

```bash
# Clone or navigate to project
cd c:/StreamLit

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

```bash
# Create .env from template
cp .env.example .env

# Edit .env with your Gemini API key
# GOOGLE_API_KEY=your_key_here
```

## Running the App

```bash
# Start Streamlit
streamlit run app.py

# App will open at http://localhost:8501
```

## Using the App

### 1. Select Your Role (Sidebar)
- **Operator**: Machine operations & safety questions
- **Engineer**: Technical diagnostics & maintenance
- **Supervisor**: Shift coordination & overview
- **Plant Manager**: Strategic KPIs & financial

### 2. Create or Load a Chat
- Click "➕ New Chat" to start
- Select from "Saved Chats" to resume
- Chat history is saved automatically per role

### 3. Ask Questions
Examples:
- "What does error code E17 mean?"
- "Create a maintenance ticket for machine MX-204"
- "What's the current status of MX-204?"
- "Generate a shift summary for today"

### 4. View Tickets (Tab: 📋 Tickets)
See all maintenance tickets created by the assistant

---

## Architecture at a Glance

### Memory System (3-Tier)
1. **Session Memory** (50 messages, current session only)
2. **Long-Term Memory** (persistent, per-role database)
3. **State Checkpointing** (resume conversations, per-role)

### Guardrails (3 Layers)
1. **Input Validation** (length, dangerous patterns)
2. **Tool Validation** (Pydantic schemas)
3. **Output Validation** (response quality)

### Tools (12 Available)
- Machine status checks
- Error code lookup
- Ticket creation
- Shift summaries
- Technician availability
- Maintenance planning

---

## File Structure

```
c:/StreamLit/
├── app.py                          # Main entry point
├── pages/
│   ├── 1_💬_Chat.py               # Chat interface
│   ├── 2_📊_Conversations.py       # Chat management
│   └── 3_📋_Tickets.py             # Ticket viewer
├── src/
│   ├── agent_engine.py             # Main agent class
│   ├── tools.py                    # 12 tools with validation
│   ├── guardrails_middleware_layer.py  # Guardrails factory
│   ├── config.py                   # Configuration
│   ├── models.py                   # Pydantic models
│   └── mcp_ticket_server.py        # Ticket persistence
├── data/
│   ├── machines.json               # Machine specs
│   ├── error_codes.json            # Error reference
│   ├── technicians.json            # Staff info
│   └── maintenance_tickets.json    # Created tickets
├── chat_history/                   # Saved chats (auto-created)
├── ARCHITECTURE.md                 # System design
├── IMPLEMENTATION_STATUS.md        # Status
└── requirements.txt
```

---

## Key Features

✅ Role-based responses (4 user types)  
✅ Multi-role chat management  
✅ 12 manufacturing tools  
✅ Guardrails & input validation  
✅ Ticket creation & persistence  
✅ Chat history per role  
✅ Conversation memory (50 messages)  

---

## Troubleshooting

### Streamlit not starting
```bash
# Install/upgrade Streamlit
pip install --upgrade streamlit
```

### Gemini API errors
- Verify GOOGLE_API_KEY in .env
- Check API quota at Google Cloud Console

### Memory issues
- Long-term memory requires langgraph:
  ```bash
  pip install langgraph
  ```
- App works without it (logs warnings)

---

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
black src/
isort src/
flake8 src/
```

### Debugging
- Streamlit logs go to console
- Agent logs written to debug_trace.txt
- Chat history saved in chat_history/{role}/

---

## Next Steps

1. **Test tool calling**: Ask agent to create a ticket
2. **Switch roles**: Verify separate chat histories
3. **Store memories**: Use long-term memory API
4. **Load test**: Simulate multiple operators

---

**Current Status**: MVP Complete (Level 1)  
**Next Phase**: Level 2 Tool Calling Validation  
**Last Updated**: 2026-07-28
