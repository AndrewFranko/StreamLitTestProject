# LangGraph Studio Setup Guide

## What is LangGraph Studio?

**LangGraph Studio** is the first IDE designed specifically for agent development. It provides:

- 🎨 **Visual Graph Editor** - See your multi-agent workflow as an interactive diagram
- 🐛 **Interactive Debugger** - Step through agent execution, pause, inspect state
- 🔄 **Live Code Iteration** - Edit code and replay agents instantly
- ⚡ **Real-Time Streaming** - Watch agent reasoning and tool calls as they happen
- ⏮️ **Time Travel Debugging** - Replay from any checkpoint, modify state
- 📊 **State Inspection** - See exactly what data flows between agents

## Installation

### Prerequisites
- LangSmith account (free)
- Python 3.10+
- LangGraph installed (`pip install langgraph`)

### Step 1: Download LangGraph Studio

Visit: https://github.com/langchain-ai/langgraph-studio

Download for your OS:
- **macOS (Apple Silicon)** - Available now
- **Windows/Linux** - Coming soon

### Step 2: Create `langgraph.json` Config

In your project root (`c:/StreamLit/`), create `langgraph.json`:

```json
{
  "graphs": {
    "level3_v2": {
      "entry": "src/level3_multi_agent_workflow_v2:execute_workflow"
    }
  }
}
```

Or for multiple workflows:

```json
{
  "graphs": {
    "level3_v2": {
      "entry": "src/level3_multi_agent_workflow_v2:execute_workflow"
    },
    "rag_pipeline": {
      "entry": "src/rag_pipeline:find_similar_tickets"
    },
    "level3_original": {
      "entry": "src/level3_multi_agent_workflow:execute_workflow"
    }
  }
}
```

### Step 3: Start LangGraph Studio

1. Open LangGraph Studio desktop app
2. Click "Open Directory"
3. Select `c:/StreamLit/`
4. Log in with LangSmith account
5. See your graphs in the sidebar

### Step 4: Run Your Workflow

```
Input: "Machine MX-204 stopped with error E17"
↓
[Visualizer shows graph structure]
↓
[Click "Run" or "Debug"]
↓
Watch real-time execution with state updates
```

## Using LangGraph Studio

### 1. Graph Visualization

Your workflow appears as:

```
┌──────────────────────────────┐
│     START (User Input)       │
│  "Machine MX-204 error E17"  │
└──────────────┬───────────────┘
               │
        ┌──────▼───────┐
        │   Agent 1    │
        │ Fault Analysis│
        └──────┬───────┘
               │
        ┌──────▼───────────┐
        │   Agent 2        │
        │ Diagnosis        │
        └──────┬───────────┘
               │
        ┌──────▼──────────┐
        │   Agent 3       │
        │ Request/Approval│
        └──────┬──────────┘
               │
        ┌──────▼──────────┐
        │      END        │
        │ awaiting_approval│
        └─────────────────┘
```

### 2. Interactive Debugging

While workflow runs:
- ⏸️ **Pause** - Interrupt at any node
- 🔍 **Inspect** - See full state at each step
- ✏️ **Modify** - Change state values mid-execution
- ▶️ **Resume** - Continue from modified state
- ⏪ **Replay** - Re-run from any checkpoint

### 3. State Inspector

For each node, see:

```
Node: Agent 2 (Diagnosis)
Status: ✓ Completed (0.8s)

Input State:
{
  "fault_analysis": {
    "machine_id": "MX-204",
    "error_code": "E17"
  },
  "messages": [...]
}

Output State:
{
  "diagnosis": {
    "severity": "high",
    "root_cause": "pump seal",
    "recommended_action": "Inspect pump"
  },
  "messages": [...]
}
```

### 4. Live Code Iteration

1. Edit your agent code in VS Code
2. Save the file
3. LangGraph Studio detects change
4. Click "Replay from Agent 1" to test
5. See new results instantly

No need to restart - iterate in real time!

## Features for Level 3 Workflow

### What You'll See

#### Agent 1: Fault Analysis
```
┌─ Think: Extract machine info ─┐
│ LLM Call: "Extract JSON..."   │
│ Output: {machine_id, error}   │
└───────────────────────────────┘
```

#### Agent 2: Diagnosis
```
┌─ Think: Analyze fault ─────────┐
│ Tool: search_machine(MX-204)   │
│   → Hydraulic Press B          │
│ Tool: lookup_error_code(E17)   │
│   → High severity              │
│ Output: {severity, action}     │
└───────────────────────────────┘
```

#### Agent 3: Request
```
┌─ Decide: Set approval ─────────┐
│ Decision: awaiting_approval    │
│ Output: {awaiting_approval}    │
└───────────────────────────────┘
```

### Time Travel Debugging

Example: Agent 2 found wrong severity?

1. In Studio, click Agent 2 in graph
2. See state before/after
3. Click "Replay from Agent 1"
4. Modify input state
5. Run again with new values
6. No need to restart whole workflow

## Integration with LangSmith

### Tracing in LangSmith Studio

LangGraph Studio shows local traces, while LangSmith shows:
- 📊 Historical runs across time
- 📈 Performance metrics and latency
- 🔗 Cross-run comparisons
- 👥 Shared team insights

### Complete Workflow:

```
Local Development:
  VS Code + LangGraph Studio
  ↓ (debug, iterate, replay)
  ↓ (step through agents)
  ↓ (modify state mid-run)
  ↓ (perfect the logic)

Production Monitoring:
  LangSmith Studio
  ↓ (see all runs)
  ↓ (compare performance)
  ↓ (identify issues)
  ↓ (replay in LangGraph Studio)
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Space` | Play/Pause |
| `S` | Step to next node |
| `R` | Replay from current node |
| `I` | Inspect state |
| `D` | Toggle debug mode |
| `⌘/Ctrl + K` | Command palette |

## Example Workflow in Studio

### Run 1: Normal execution
```
Input: "Machine MX-204 error E17"
↓
Agent 1 completes (1.2s)
↓
Agent 2 completes (0.8s)
  Tool calls visible: search_machine, lookup_error_code
↓
Agent 3 completes (0.1s)
↓
Total: 2.1s ✓
```

### Run 2: Debug with state modification
```
Input: "Machine MX-204 error E17"
↓
Agent 1 completes → ⏸ Pause here
↓
[Modify state] Change severity to "critical"
↓
▶ Resume from Agent 2
↓
Agent 2 sees modified input
↓
Agent 3 generates different recommendation
↓
Compare both outputs in inspector
```

## Troubleshooting

### "Cannot find workflow" error
- Check `langgraph.json` syntax
- Verify file path is correct
- Ensure function is exported in Python file

### "Connection refused" 
- Make sure LangSmith account is active
- Check API key in environment
- Try logging out/in in Studio

### Changes not reloading
- Save Python file (VS Code auto-save)
- Wait 2 seconds for Studio to detect
- Click refresh if needed
- Replay from desired node

## For FactoryOps AI Project

### Setup Steps

1. **Create `langgraph.json`**:
```bash
cat > c:/StreamLit/langgraph.json << 'EOF'
{
  "graphs": {
    "level3_v2": {
      "entry": "src/level3_multi_agent_workflow_v2:execute_workflow"
    }
  }
}
EOF
```

2. **Open in Studio**:
   - Launch LangGraph Studio
   - File → Open Directory → `c:/StreamLit/`
   - See Level 3 workflow graph

3. **Test Agent Flow**:
   - Input: "Machine MX-204 stopped with error E17"
   - Watch Agent 1 → Agent 2 → Agent 3 execute
   - Inspect state at each node
   - See message history accumulate

4. **Debug Agent Reasoning**:
   - Pause at Agent 2
   - Inspect what it found
   - Modify state to test edge cases
   - Replay to see new behavior

## Comparison: Local vs Cloud Debugging

| Feature | LangGraph Studio (Local) | LangSmith Studio (Cloud) |
|---------|-------------------------|--------------------------|
| **Real-time debugging** | ✅ Yes | ❌ No |
| **Step through execution** | ✅ Yes | ❌ No |
| **Modify state mid-run** | ✅ Yes | ❌ No |
| **See all historical runs** | ❌ No | ✅ Yes |
| **Performance metrics** | ❌ No | ✅ Yes |
| **Team collaboration** | ❌ No | ✅ Yes |
| **Agent graph visualization** | ✅ Yes | ✅ Yes |

**Best Practice**: Use both!
- **LangGraph Studio** for development & debugging
- **LangSmith Studio** for monitoring & analysis

## Resources

- [LangGraph Studio Official Blog](https://www.langchain.com/blog/langgraph-studio-the-first-agent-ide)
- [GitHub Repository](https://github.com/langchain-ai/langgraph-studio)
- [Installation Guide](https://markaicode.com/langgraph-studio-visual-debugger-agent-graphs/)
- [Advanced Debugging](https://mem0.ai/blog/visual-ai-agent-debugging-langgraph-studio)

## Next Steps

1. ✅ Install LangGraph Studio
2. ✅ Create `langgraph.json` in project root
3. ✅ Open FactoryOps AI project in Studio
4. ✅ Run Level 3 workflow v2
5. ✅ Debug agent reasoning with visual inspector
6. ✅ Integrate LangSmith for production monitoring

