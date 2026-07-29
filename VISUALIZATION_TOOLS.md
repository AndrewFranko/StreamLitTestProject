# Agent Flow Visualization Tools

## Complete Visualization Stack for FactoryOps AI

```
Your Agent Code
    ↓
    ├─→ LangGraph Studio (Local IDE) ← Development & Debugging
    │   ├─ Visual graph editor
    │   ├─ Step-by-step debugging
    │   ├─ State inspection
    │   └─ Live code iteration
    │
    ├─→ LangSmith Studio (Cloud) ← Monitoring & Analysis
    │   ├─ Historical traces
    │   ├─ Performance metrics
    │   ├─ Agent graph visualization
    │   └─ Team collaboration
    │
    └─→ Mermaid Diagrams (Documentation) ← Understanding
        ├─ Agent architecture
        ├─ State flow
        ├─ Tool usage
        └─ Decision trees
```

---

## 1. LangGraph Studio (Local Development)

### What It Does
Visual IDE for debugging multi-agent workflows **locally** on your machine.

### Best For
- 🐛 **Debugging** - Step through agent execution
- 🔍 **Inspecting** - See state at each node
- ✏️ **Experimenting** - Modify state mid-run
- 🔄 **Iterating** - Edit code and replay instantly
- 📚 **Learning** - Understand how agents think

### Install

**macOS (Apple Silicon)**:
```bash
# Download from GitHub
https://github.com/langchain-ai/langgraph-studio
# Then follow LANGGRAPH_STUDIO_SETUP.md
```

**Windows/Linux**: Coming soon (2026)

### Usage Example

```
1. Open LangGraph Studio
2. File → Open Directory → c:/StreamLit/
3. See Level 3 workflow as visual graph
4. Input: "Machine MX-204 error E17"
5. Click Debug
6. Watch agents execute in real-time
7. Pause at any agent
8. Inspect state: {"fault_analysis": {...}, "diagnosis": {...}}
9. Modify severity from "high" to "critical"
10. Resume and see different outcome
```

### Key Features

| Feature | Benefit |
|---------|---------|
| **Graph Visualization** | Understand workflow structure |
| **Real-time Streaming** | See agent decisions as they happen |
| **State Inspection** | Debug exactly what data flows |
| **Time Travel** | Replay from any checkpoint |
| **Live Code Iteration** | Edit and test without restart |
| **Step Debugging** | Pause after each node |

### Architecture View in Studio

```
┌─────────────────────────────────┐
│   Agent 1: Fault Analysis       │
│   Status: ✓ (1.2s)              │
│   Input: {user_input}           │
│   Output: {fault_analysis}      │
│   ⏸ Pause | ▶ Resume | 🔄 Replay │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│   Agent 2: Diagnosis            │
│   Status: ⏸ (paused)            │
│   Input: {fault_analysis}       │
│   Output: {diagnosis}           │
│   Tools Called:                 │
│   - search_machine(MX-204)      │
│   - lookup_error_code(E17)      │
│   ⏸ Pause | ▶ Resume | 🔄 Replay │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│   Agent 3: Request              │
│   Status: ⏳ (pending)           │
│   Input: {diagnosis}            │
│   Output: {awaiting_approval}   │
│   ⏸ Pause | ▶ Resume | 🔄 Replay │
└─────────────────────────────────┘
```

---

## 2. LangSmith Studio (Cloud Monitoring)

### What It Does
Cloud-based observability platform for monitoring **production** agent workflows.

### Best For
- 📊 **Monitoring** - Track all production runs
- 📈 **Analytics** - Performance metrics and latency
- 🔗 **Comparison** - Compare different runs
- 👥 **Collaboration** - Share insights with team
- 🎯 **Optimization** - Identify bottlenecks

### Setup

**Free Account**:
```bash
1. Go to https://smith.langchain.com
2. Sign up (free)
3. Create API key
4. Add to .env:
   LANGSMITH_API_KEY=<your_key>
   LANGSMITH_PROJECT=factoryops
   LANGCHAIN_TRACING_V2=true
```

### Usage Example

```
1. Open https://smith.langchain.com/studio
2. Select project: "factoryops"
3. See all traces from your agents
4. Click on trace to see:
   - Full execution timeline
   - All tool calls with inputs/outputs
   - State transitions
   - Latency breakdown
5. Compare runs side-by-side
```

### Dashboard View

```
Project: factoryops

Recent Runs (100 total)
├─ Run #100: Level 3 - MX-204 E17
│  ├─ Status: ✓ Success
│  ├─ Duration: 2.1s
│  ├─ Tokens: 450 (input), 230 (output)
│  ├─ Agent 1: 1.2s
│  ├─ Agent 2: 0.8s
│  └─ Agent 3: 0.1s
│
├─ Run #99: Level 3 - MX-105 E23
│  ├─ Status: ✓ Success
│  ├─ Duration: 1.9s
│  └─ ...
│
└─ Run #98: RAG Pipeline
   ├─ Status: ⚠️ Slow
   ├─ Duration: 5.2s
   └─ ...
```

### Key Features

| Feature | Benefit |
|---------|---------|
| **Historical Tracing** | See all production runs |
| **Performance Metrics** | Latency, tokens, costs |
| **Agent Graph View** | Visualize workflow structure |
| **Comparison Tool** | Compare run performance |
| **Alerting** | Get notified of issues |
| **Team Access** | Share with team |

---

## 3. Mermaid Diagrams (Documentation)

### What It Does
Create **static architecture diagrams** in markdown format.

### Best For
- 📚 **Documentation** - Explain architecture
- 🎓 **Learning** - Understand concepts
- 🔧 **Design** - Plan before coding
- 📋 **Communication** - Share with team
- 🎨 **Visualization** - Visual reference

### Examples in Project

```
AGENT_ARCHITECTURE.md includes:
├─ v1 vs v2 comparison
├─ Agent 1: Fault Analysis flow
├─ Agent 2: Diagnosis flow (with loop)
├─ State flow through agents
├─ Tool usage comparison
└─ LangSmith trace structure
```

### Render Options

**GitHub** (renders automatically):
```markdown
# See diagrams in GitHub repo
```

**Local** (VS Code extension):
```bash
# Install "Markdown Preview Mermaid Support"
# Then Ctrl+Shift+V to preview
```

**Online Tools**:
- https://mermaid.live - Web editor
- https://mermaid.ink - Create PNG/SVG

---

## Complete Workflow: Development to Production

### Phase 1: Design (Mermaid)
```
Create AGENT_ARCHITECTURE.md
├─ Diagram agent flow
├─ Show state transitions
├─ Plan tool usage
└─ Review with team
```

### Phase 2: Development (LangGraph Studio)
```
Open LangGraph Studio
├─ Load project
├─ Run workflows
├─ Debug agents
├─ Modify state mid-run
├─ Iterate rapidly
└─ Verify behavior
```

### Phase 3: Deployment (LangSmith)
```
Deploy to production
├─ Set LANGSMITH_API_KEY
├─ Enable LANGCHAIN_TRACING_V2=true
├─ Monitor traces in Studio
├─ Track performance
├─ Identify issues
└─ Optimize based on metrics
```

---

## Tool Comparison Matrix

| Aspect | LangGraph Studio | LangSmith | Mermaid |
|--------|-----------------|-----------|---------|
| **Cost** | Free | Free tier + paid | Free |
| **Real-time Debug** | ✅ Yes | ❌ No | ❌ No |
| **Step Through** | ✅ Yes | ❌ No | ❌ No |
| **Modify State** | ✅ Yes | ❌ No | ❌ No |
| **Historical Data** | ❌ No | ✅ Yes | ❌ No |
| **Team Sharing** | ❌ No | ✅ Yes | ✅ Yes |
| **Metrics/Analytics** | ❌ Basic | ✅ Advanced | ❌ No |
| **Local** | ✅ Yes | ❌ Cloud | ✅ Yes |
| **Graph Viz** | ✅ Interactive | ✅ Interactive | ✅ Static |
| **Best For** | Development | Production | Docs |

---

## For FactoryOps AI Project

### Recommended Setup

```
Development:
  VS Code + LangGraph Studio
  └─ LANGGRAPH_STUDIO_SETUP.md

Testing:
  pytest + manual testing
  └─ tests/ directory

Documentation:
  Markdown + Mermaid
  └─ AGENT_ARCHITECTURE.md

Monitoring:
  LangSmith Studio + .env config
  └─ LANGSMITH_SETUP.md
```

### Quick Start Commands

```bash
# 1. Setup LangSmith tracing
cat > .env << 'EOF'
LANGSMITH_API_KEY=<your_api_key>
LANGSMITH_PROJECT=factoryops
LANGCHAIN_TRACING_V2=true
EOF

# 2. Create LangGraph Studio config
cat > langgraph.json << 'EOF'
{
  "graphs": {
    "level3_v2": {
      "entry": "src/level3_multi_agent_workflow_v2:execute_workflow"
    }
  }
}
EOF

# 3. Open LangGraph Studio
# Download from https://github.com/langchain-ai/langgraph-studio
# Then: File → Open Directory → c:/StreamLit/

# 4. Monitor in LangSmith
# Go to https://smith.langchain.com/studio
# Select project: factoryops
```

---

## Next Steps

1. ✅ Read `AGENT_ARCHITECTURE.md` - Understand architecture
2. ✅ Read `LANGGRAPH_STUDIO_SETUP.md` - Setup local debugging
3. ✅ Read `LANGSMITH_SETUP.md` - Setup cloud monitoring
4. ✅ Install LangGraph Studio - Start debugging locally
5. ✅ Create `.env` with LangSmith key - Enable tracing
6. ✅ Run Level 3 workflow - See traces in both tools
7. ✅ Debug with Studio - Step through agents
8. ✅ Monitor in LangSmith - Track production performance

---

## Resources

- [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio) - Download & docs
- [LangSmith Studio](https://smith.langchain.com) - Cloud monitoring
- [Mermaid.js](https://mermaid.js.org) - Diagram syntax
- [LangChain Docs](https://python.langchain.com) - API reference

