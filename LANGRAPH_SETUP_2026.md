# LangGraph Server Setup - FactoryOps AI (2026)

## ✅ Current Status

Your server now implements the **LangGraph Server API Protocol (2026)** with full support for:
- ✅ Multi-agent workflow (3 agents: Fault Analysis → Diagnosis → Request)
- ✅ LangGraph Studio visualization
- ✅ LangSmith tracing and monitoring
- ✅ Streamlit integration at port 8501

---

## 📍 Server Configuration

**FastAPI Server Running At:**
```
http://localhost:8080
```

**Streamlit App Running At:**
```
http://localhost:8501
```

**LangSmith Monitoring At:**
```
https://eu.smith.langchain.com/studio
Project: Factory
```

---

## 🔗 Implemented Endpoints (LangGraph Server API 2026)

### 1. **POST /assistants/search**
Find and list available agents/workflows.

**Response:**
```json
{
  "assistants": [
    {
      "assistant_id": "f011a49e-29bc-57d6-b04e-54bf437bff4a",
      "graph_id": "level3_workflow",
      "name": "Level 3 Multi-Agent Workflow",
      "description": "Multi-agent fault handling...",
      "config": {
        "tags": ["multi-agent", "manufacturing", "fault-handling"],
        "recursion_limit": 25,
        "configurable": {}
      },
      "metadata": {
        "type": "multi_agent",
        "nodes": ["fault_analysis", "diagnosis", "request"],
        "agents": 3,
        "flow": "sequential"
      }
    }
  ],
  "pagination": {
    "limit": 10,
    "offset": 0,
    "total": 1
  }
}
```

### 2. **GET /assistants/{id}/schemas**
Get input/output type definitions for Studio introspection.

**Response:**
```json
{
  "input_schema": {
    "type": "object",
    "properties": {
      "user_input": {"type": "string"},
      "messages": {"type": "array"}
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "fault_analysis": {"type": "object"},
      "diagnosis": {"type": "object"},
      "awaiting_approval": {"type": "boolean"},
      "ticket_created": {"type": "boolean"}
    }
  },
  "state_schema": { ... }
}
```

### 3. **GET /assistants/{id}/graph**
Get graph topology for visualization.

**Response:**
```json
{
  "id": "level3_workflow",
  "name": "Level 3 Workflow",
  "type": "compiled_state_graph",
  "nodes": [
    {
      "id": "fault_analysis",
      "label": "Fault Analysis Agent",
      "type": "agent",
      "position": {"x": 0, "y": 0}
    },
    {
      "id": "diagnosis",
      "label": "Diagnosis Agent",
      "type": "agent",
      "position": {"x": 400, "y": 0}
    },
    {
      "id": "request",
      "label": "Request Agent",
      "type": "agent",
      "position": {"x": 800, "y": 0}
    }
  ],
  "edges": [
    {"source": "fault_analysis", "target": "diagnosis"},
    {"source": "diagnosis", "target": "request"}
  ]
}
```

### 4. **POST /invoke**
Execute the workflow with input.

**Request:**
```json
{
  "input": "Machine MX-204 error E17"
}
```

**Response:**
```json
{
  "status": "success",
  "output": {
    "user_input": "Machine MX-204 error E17",
    "fault_analysis": { ... },
    "diagnosis": { ... },
    "awaiting_approval": true,
    "ticket_created": false
  }
}
```

---

## 🔍 How to Connect

### **Option A: LangGraph Studio (Recommended)**

1. Go to: `https://smith.langchain.com/studio` (or EU: `https://eu.smith.langchain.com/studio`)
2. Enter endpoint: `http://localhost:8080`
3. Studio will:
   - Fetch assistants from `/assistants/search`
   - Load graph topology from `/assistants/{id}/graph`
   - Allow you to run/debug workflows visually

### **Option B: Direct API Calls**

```bash
# Test the server
curl http://localhost:8080/health

# Invoke workflow
curl -X POST http://localhost:8080/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": "Machine MX-204 error E17"}'

# Get assistant info
curl http://localhost:8080/assistants/search
```

### **Option C: Streamlit App (UI)**

Open `http://localhost:8501` in browser and navigate to:
- 📊 Dashboard for status overview
- 🔧 Fault Handling workflow
- 💬 Chat interface

---

## 📊 LangSmith Integration

### **Monitoring Traces**

1. Go to: `https://eu.smith.langchain.com`
2. Select Project: `Factory`
3. View traces from your workflow executions

### **What Gets Traced**
- Each agent execution (fault_analysis, diagnosis, request)
- LLM calls to Gemini
- Tool invocations (machine search, error lookup)
- Complete state transitions

### **Environment Variables**
```ini
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=Factory
LANGCHAIN_TRACING_V2=true
LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

---

## 🏗️ Architecture

### **Multi-Agent Workflow**

```
User Input
    ↓
[Fault Analysis Agent]
  ├─ Extracts: machine_id, error_code
  ├─ Validates: required fields present
  └─ Output: fault_analysis dict
    ↓
[Diagnosis Agent]
  ├─ Tool: search_machine(machine_id)
  ├─ Tool: lookup_error_code(error_code)
  ├─ Determines: severity, root_cause, recommendation
  └─ Output: diagnosis dict
    ↓
[Request Agent]
  ├─ Presents: recommendation to human
  ├─ Awaits: human approval
  ├─ Tool: create_maintenance_ticket()
  └─ Output: ticket_created flag
    ↓
Response to User
```

### **State Flow**

```python
{
  "user_input": str,
  "messages": list[Message],
  "fault_analysis": {
    "machine_id": str,
    "error_code": str,
    "request_type": str
  },
  "diagnosis": {
    "machine_details": dict,
    "error_details": dict,
    "severity": str,
    "root_cause": str,
    "recommended_action": str
  },
  "awaiting_approval": bool,
  "ticket_created": bool,
  "error": str | None
}
```

---

## 📝 Example Workflow Execution

### **Input**
```
"Machine MX-204 stopped with error E17"
```

### **Agent 1: Fault Analysis**
- Extracts: machine_id="MX-204", error_code="E17"
- Validates: Both fields present ✓
- Output: `{"machine_id": "MX-204", "error_code": "E17", ...}`

### **Agent 2: Diagnosis**
- Searches: Machine MX-204 = Hydraulic Press B
- Looks up: E17 = Hydraulic pressure loss
- Determines: Severity=HIGH, Cause=Seal failure, Action=Inspect lines
- Output: `{"severity": "high", "recommended_action": "...", ...}`

### **Agent 3: Request**
- Presents: "Machine MX-204 has HIGH severity issue. Recommend: Inspect hydraulic lines, check pump pressure"
- Sets: `awaiting_approval=true`
- Awaits: Human approval (from Streamlit UI)
- On approval: Creates ticket, sets `ticket_created=true`

---

## 🚀 Running Everything

### **Terminal 1: Start FastAPI Server**
```bash
cd c:/StreamLit
python src/langgraph_server.py
# Starts at http://localhost:8080
```

### **Terminal 2: Start Streamlit App**
```bash
cd c:/StreamLit
streamlit run app.py
# Starts at http://localhost:8501
```

### **Terminal 3: Monitor LangSmith**
Go to: `https://eu.smith.langchain.com/studio`

---

## ✅ Verification Checklist

- [x] FastAPI server starts without errors
- [x] `/assistants/search` returns proper format
- [x] `/assistants/{id}/schemas` provides type definitions
- [x] `/assistants/{id}/graph` returns topology with 3 nodes
- [x] `/invoke` executes workflow and shows all 3 agents
- [x] Streamlit app connects to backend
- [x] LangSmith receives traces from workflow
- [x] Human approval flow works in Streamlit
- [x] Tickets are created after approval

---

## 🔗 Key References

- **LangGraph Server API 2026**: [docs.langchain.com/langsmith/agent-server](https://docs.langchain.com/langsmith/agent-server)
- **Agent Protocol**: [github.com/langchain-ai/agent-protocol](https://github.com/langchain-ai/agent-protocol)
- **LangSmith Tracing**: [docs.langchain.com/langsmith/observability](https://docs.langchain.com/langsmith/observability)
- **LangGraph Examples**: [github.com/langchain-ai/langgraph-example](https://github.com/langchain-ai/langgraph-example)

---

**Last Updated:** 2026-07-29  
**Status:** ✅ Production Ready (Level 3 Complete)
