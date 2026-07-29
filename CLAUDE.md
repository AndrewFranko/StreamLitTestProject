# FactoryOps AI – Manufacturing Assistant

**Project**: AI-powered Manufacturing Assistant for FactoryOps Manufacturing  
**Client**: FactoryOps Manufacturing (5 plants, 3,500 employees, 250 machines, 24x7 operations)  
**Tech Stack**: LangChain + Gemini API + Streamlit  
**Status**: MVP Planning (Level 1-4 Progressive Development)

---

## Project Overview

FactoryOps AI is a multi-phased, role-based manufacturing assistant serving 4 user groups:

1. **Machine Operators** — Quick answers on procedures, error codes, safety checks
2. **Maintenance Engineers** — Diagnostic workflows, ticket creation, technician coordination
3. **Production Supervisors** — Real-time status, downtime tracking, shift summaries
4. **Plant Managers** — Strategic KPIs, production visibility, AI-assisted operations

### Executive Goals

- Reduced machine downtime
- Faster maintenance response times
- Improved operator productivity
- Enhanced production visibility
- AI-assisted plant operations

---

## Architecture Overview

### Four-Level Progressive Development

#### **Level 1: Conversational Manufacturing Assistant** (MVP)

- **Scope**: LLM-powered chatbot with manufacturing domain knowledge
- **Users**: Machine operators asking about procedures, error codes, safety
- **Technology**:
  - LangChain `ChatGoogleGenerativeAI` (Gemini)
  - ConversationBufferMemory for session context
  - Prompt templates for role-based responses
  - Streamlit chat interface

- **Learner Deliverables**:
  - Chat UI with message history
  - Manufacturing persona with guardrails
  - Session-scoped memory (operators, engineers, supervisors)
  - Prompt templates for domain knowledge
  - Basic input validation

- **Key Questions Handled**:
  - Operating procedures for specific machines
  - Error code explanations (E17, E23, etc.)
  - Safety check procedures
  - Production target clarification
  - Shift handover instructions

---

#### **Level 2: Single AI Agent with Tool Calling**

- **Scope**: Transform chatbot into an agent that performs actions
- **Action Tools**:
  - `check_machine_status(machine_id)` → fetch live machine data
  - `lookup_error_code(error_code)` → explain fault codes
  - `create_maintenance_ticket(machine_id, description, priority)` → generate tickets
  - `check_technician_availability(specialty)` → find available maintenance staff
  - `generate_shift_summary(shift_id)` → produce end-of-shift reports
  - `escalate_critical_failure(machine_id, reason)` → alert supervisors

- **Agent Loop**:
  - User query → LLM interprets intent
  - LLM decides which tool(s) to invoke
  - Tool execution returns data
  - LLM synthesizes response

- **Human-in-the-Loop** (stretch):
  - For critical failures: ask supervisor for approval before shutdown

- **Technology**:
  - LangChain `AgentExecutor`
  - Tool definitions with JSON schemas
  - Output parsers for structured responses
  - Conversation memory across tool calls

---

#### **Level 3: Multi-Agent Architecture (Machine Fault Handling)**

Workflows like: *"Machine MX-204 stopped with error E17. Check issue and create maintenance request."*

**Agent 1: Fault Analysis Agent**
- Extracts: machine_id, error_code, requested_action
- Validates completeness
- Output: Structured JSON with parsed fields

**Agent 2: Maintenance Diagnosis Agent**
- Tools:
  - `search_machine(machine_id)` → JSON file lookup
  - `lookup_error_code(error_code)` → JSON file lookup
- Determines: severity level, root cause, recommended action
- Output: Diagnostic report + maintenance recommendation

**Agent 3: Maintenance Request Agent**
- Presents recommendation to user
- Pauses for human approval
- Tool: `create_maintenance_ticket(...)` → append to JSON or database
- Output: Confirmation with ticket ID

**Data Sources** (initially JSON files, later REST APIs):
- `machines.json` — Machine specs, current status, location
- `error_codes.json` — Error → symptom → recommended_fix mappings
- `technicians.json` — Available staff, specialties, current workload

---

#### **Level 4: Streamlit Web Deployment**

- **Frontend**: Role-based Streamlit UI
- **Backend**: FastAPI or Streamlit native for API integration
- **Environment**: `.env` configuration for Gemini API key, system endpoints
- **Data Persistence**: SQLite or PostgreSQL for chat history, tickets
- **Production Readiness**:
  - Logging and audit trails
  - Error monitoring and alerting
  - Rate limiting and request validation
  - Docker containerization

---

## Technology Stack

### Core Dependencies

```
langchain >= 0.1.0
langchain-google-genai >= 0.0.10
google-generativeai >= 0.4.0
streamlit >= 1.28.0
python-dotenv >= 1.0.0
pydantic >= 2.0.0
```

### Optional (Level 3+)

```
langgraph >= 0.0.1
sqlalchemy >= 2.0.0
fastapi >= 0.104.0
uvicorn >= 0.24.0
```

### Recommended Structure

```
factoryops-ai/
├── .env.example                    # Template (no secrets)
├── .env                            # Local (gitignored)
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── config.py                   # Load .env, app settings
│   ├── models.py                   # Pydantic schemas
│   │
│   ├── level1_chatbot/
│   │   ├── chat_engine.py          # LangChain chat logic
│   │   ├── prompts.py              # System prompts by role
│   │   └── memory.py               # Conversation memory
│   │
│   ├── level2_agent/
│   │   ├── agent.py                # AgentExecutor setup
│   │   └── tools/
│   │       ├── machine_status.py
│   │       ├── error_lookup.py
│   │       ├── ticket_creation.py
│   │       └── technician_checker.py
│   │
│   ├── level3_multi_agent/
│   │   ├── agents/
│   │   │   ├── fault_analysis.py
│   │   │   ├── maintenance_diagnosis.py
│   │   │   └── request_handler.py
│   │   ├── tools/
│   │   │   ├── machine_search.py
│   │   │   └── error_search.py
│   │   └── workflow.py             # Orchestration logic
│   │
│   ├── data/
│   │   ├── machines.json           # Mock machine data
│   │   ├── error_codes.json        # Error code reference
│   │   └── technicians.json        # Staff availability
│   │
│   └── ui/
│       └── streamlit_app.py        # Level 4 web interface
│
├── tests/
│   ├── test_level1_chat.py
│   ├── test_level2_agent.py
│   ├── test_level3_workflow.py
│   └── test_integration.py
│
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## Environment Configuration

### `.env` Template

```ini
# Gemini API
GOOGLE_API_KEY=your_gemini_key_here

# Application
APP_ENV=development  # development, staging, production
APP_NAME=FactoryOps AI
LOG_LEVEL=INFO

# Database (Level 3+)
DATABASE_URL=sqlite:///./data/factory_ops.db

# API Integration (Level 2+)
MES_API_URL=http://mes-internal.factoryops.com/api
MAINTENANCE_API_URL=http://maintenance.factoryops.com/api
INVENTORY_API_URL=http://inventory.factoryops.com/api

# Session & Security
SESSION_TIMEOUT_MINUTES=30
MAX_CONVERSATION_LENGTH=100

# Monitoring
SENTRY_DSN=  # Optional error tracking
```

### Loading Configuration

```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_api_key: str
    app_env: str = "development"
    database_url: str = "sqlite:///./factory_ops.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

---

## User Interface Design

### Role-Based UX Strategy

#### **Machine Operator Interface** (Shift Worker)
- **Goal**: Quick answers on-the-job
- **Layout**:
  - Large chat input box (mobile-friendly)
  - Quick-action buttons: "Check My Machine", "Report Error", "Shift Notes"
  - Minimal navigation
  - Visual error code explanations (red/yellow/green severity indicators)
  - One-step ticket creation for urgent issues
- **Customization**:
  - Operator persona in system prompt
  - Simplified maintenance language
  - Safety reminders when appropriate

#### **Maintenance Engineer Interface**
- **Goal**: Diagnostic depth and workflow efficiency
- **Layout**:
  - Chat + right-side panel for machine details
  - Technical specs displayed inline
  - Error code + diagnostic history
  - Tool availability checker (spare parts, test equipment)
  - Multi-step workflow visualizer
  - Ticket editor (draft before submission)
- **Customization**:
  - Engineer persona with technical jargon
  - Structured diagnostic recommendations
  - History of similar issues
  - Part inventory suggestions

#### **Production Supervisor Interface**
- **Goal**: Real-time oversight and coordination
- **Layout**:
  - Dashboard: Machine status grid (red/yellow/green)
  - Current downtime summary
  - Shift handover chat
  - Quick access to shift summaries
  - Technician allocation view
  - Alert notifications (critical failures)
- **Customization**:
  - Supervisor-level access to plant-wide data
  - Shift summary generation
  - Escalation workflows
  - KPI snippets (availability %, downtime trend)

#### **Plant Manager Interface** (Executive)
- **Goal**: Strategic visibility
- **Layout**:
  - KPI dashboard: downtime %, maintenance response time, operator productivity
  - AI insights: predictive maintenance recommendations
  - Plant comparison (if multi-plant)
  - Weekly/monthly trend charts
  - Natural language query for custom reports
- **Customization**:
  - Manager-level aggregated data
  - Financial impact estimates
  - Strategic AI recommendations

### Shared Components

1. **Chat Interface**: Customizable message styling per role
2. **Error Notification**: Toast alerts for critical machine failures
3. **Loading States**: Progress indicators for multi-step workflows
4. **Authentication**: Role-based sidebar (if multi-user)
5. **Conversation Export**: Save/print chat for documentation

### Mobile & Accessibility

- Responsive design (mobile operators on factory floor)
- High contrast for industrial lighting conditions
- Keyboard navigation (hands may be occupied)
- Multilingual support (future phases)

---

## Data Flow & Integration

### Level 1-2: Internal Flow Only

```
User Input → LangChain Chat → Gemini LLM → Response
             ↓ (with tools)
          Tool Execution → Simulated/Mock Data → Response Synthesis
```

### Level 2-3: System Integration

```
User Query
    ↓
[Fault Analysis Agent] → Extracts: machine_id, error_code
    ↓
[Maintenance Diagnosis Agent]
    ├→ Tool: search_machine(machine_id) → machines.json
    ├→ Tool: lookup_error_code(error_code) → error_codes.json
    └→ Recommends action (repair, replace, inspect)
    ↓
[Maintenance Request Agent]
    ├→ Present recommendation
    ├→ Await user approval
    ├→ Tool: create_maintenance_ticket() → JSON/DB
    └→ Return confirmation
```

### Level 3+: REST API Integration

```
Maintenance Request Agent
    ├→ POST /api/tickets → MES
    ├→ GET /api/technicians?specialty=electrical → Maintenance System
    ├→ POST /api/parts/reserve → Inventory System
    └→ Webhook: notify_supervisor (Teams/Email)
```

---

## Implementation Roadmap

### Phase 1: Level 1 (MVP - Week 1-2)

**Goals**: Basic chat interface, role-based responses

- [ ] Setup LangChain + Gemini integration
- [ ] Implement conversation memory
- [ ] Create 3 system prompts (operator, engineer, supervisor)
- [ ] Build Streamlit chat UI
- [ ] Test with mock questions
- [ ] Documentation

**Success Criteria**:
- Operators get safety-focused answers
- Engineers get technical details
- Supervisors get overview insights

---

### Phase 2: Level 2 (Single Agent - Week 2-3)

**Goals**: Add tool calling, simulate backend actions

- [ ] Design tool schemas (machine status, error codes, tickets, technician availability)
- [ ] Implement mock tool functions (read from JSON files)
- [ ] Build AgentExecutor with LangChain
- [ ] Add human-in-the-loop for critical failures
- [ ] Integration tests for tool calling
- [ ] UI: Add quick-action buttons, ticket creation flow

**Success Criteria**:
- Agent correctly invokes tools based on user intent
- Tickets can be created via chat
- Critical failure escalations work

---

### Phase 3: Level 3 (Multi-Agent - Week 3-4)

**Goals**: Sequential agent workflow, structured diagnosis

- [ ] Implement 3-agent workflow (Fault Analysis → Diagnosis → Request)
- [ ] Build tool definitions for machine/error searches
- [ ] Add structured output parsing
- [ ] Create test data: machines.json, error_codes.json
- [ ] End-to-end workflow testing
- [ ] Visualization of agent reasoning

**Success Criteria**:
- Complex queries handled by multi-agent workflow
- Fault diagnostic accuracy validated
- Agent collaboration produces quality recommendations

---

### Phase 4: Level 4 (Deployment - Week 4)

**Goals**: Production-ready Streamlit app

- [ ] Finalize environment configuration
- [ ] Setup database (SQLite for testing, PostgreSQL for production)
- [ ] Add logging and monitoring
- [ ] Docker setup
- [ ] User authentication (role-based access)
- [ ] Performance testing (response time, concurrent users)
- [ ] Security review (API key handling, data privacy)

**Success Criteria**:
- App deployable in production environment
- All levels function correctly post-deployment
- 50-100 concurrent users supported

---

## Testing Strategy

### Unit Tests (Each Level)

- **Level 1**: Prompt templates produce role-specific responses
- **Level 2**: Tool invocation logic and output parsing
- **Level 3**: Agent state transitions, sequential workflow
- **Level 4**: API integration, authentication, error handling

### Integration Tests

- End-to-end workflows (user query → response)
- Multi-agent collaboration
- REST API integration (once live MES is available)

### Multi-Agent Reliability Tests

- **Agent Competence**: Each agent produces correct output for its task
- **Agent Communication**: Output from Agent A is properly consumed by Agent B
- **Error Recovery**: Graceful handling when tool calls fail
- **Edge Cases**: Missing machine IDs, unknown error codes, no available technicians

```python
# Example: Test multi-agent workflow reliability
def test_fault_analysis_to_diagnosis_handoff():
    fault_output = fault_analysis_agent(
        "Machine MX-204 error E17"
    )
    assert fault_output.machine_id == "MX-204"
    assert fault_output.error_code == "E17"
    
    diagnosis = maintenance_diagnosis_agent(
        machine_id=fault_output.machine_id,
        error_code=fault_output.error_code
    )
    assert diagnosis.severity in ["low", "medium", "high"]
    assert diagnosis.recommendation is not None
```

### Load Testing

- Simulate 50-100 concurrent operators asking questions
- Measure response latency
- Ensure memory cleanup between sessions

---

## Security Considerations

### API Key Management

- **DO NOT commit `.env` file**
- Use `.env.example` as template
- In production: use managed secrets (AWS Secrets Manager, Google Secret Manager)
- Rotate Gemini API key periodically
- Monitor API usage for anomalies

### Data Privacy

- Chat history should not be exposed across users
- Manufacturing data is sensitive (production numbers, equipment specs)
- Implement role-based access control (RBAC)
- Log all ticket creation and machine queries for audit

### Input Validation

- Validate machine IDs against known machines
- Sanitize user input (prevent prompt injection)
- Rate limit API calls per user/session
- Graceful fallback if Gemini API is unavailable

---

## Monitoring & Observability

### Key Metrics

- **Latency**: Response time per query (target: <3s for chat, <5s for multi-agent)
- **Availability**: Uptime % (target: 99.5%)
- **Tool Success Rate**: % of tool calls that succeed
- **User Satisfaction**: Per-interaction feedback
- **API Cost**: Monthly Gemini API spend

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"User {user_id} asked: {query}")
logger.debug(f"Agent selected tool: {tool_name}")
logger.warning(f"Tool failed: {tool_name} - Retrying...")
logger.error(f"Critical failure: {machine_id} - Escalating")
```

### Alerting

- Gemini API quota exceeded → Page engineer
- Tool failure rate > 10% → Investigate
- Response latency > 10s → Check LLM performance
- Critical machine failure → Notify supervisor immediately

---

## Stretch Goals & Future Enhancements

1. **Predictive Maintenance**: ML model to predict failures before they occur
2. **Multi-Plant Analytics**: Cross-plant insights and benchmarking
3. **Natural Language Reports**: Generate shift/monthly summaries automatically
4. **Mobile App**: Native iOS/Android for operators on factory floor
5. **Voice Interface**: Hands-free operation via voice commands
6. **Computer Vision**: Integrate camera feeds for visual diagnostics
7. **Collaborative Agents**: Multiple AI agents working in parallel for complex tasks
8. **Feedback Loop**: Learn from operator corrections to improve recommendations

---

## Development Workflow

### Getting Started

```bash
# Clone repo
git clone <repo-url>
cd factoryops-ai

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your Gemini API key

# Run Level 1 chatbot
streamlit run src/ui/streamlit_app.py

# Run tests
pytest tests/
```

### Branch Strategy

- `main` — Production code
- `develop` — Integration branch
- `feature/level-1-chat` — Feature branches per level
- `bugfix/` — Bug fixes

### Code Standards

- Python 3.10+
- Type hints for all functions
- Docstrings for public APIs
- PEP 8 formatting (black + isort)
- Pre-commit hooks for linting

---

## Assumptions & Constraints

### Assumptions

1. Gemini API will be available and reliable (99.9% uptime)
2. FactoryOps has REST APIs for MES, Maintenance, Inventory systems
3. Mock data (machines.json, error_codes.json) is available for testing
4. Users have basic web/chat app experience
5. Internet connectivity is stable in manufacturing facilities

### Constraints

1. **No real-time machine control** — Only read status and create tickets
2. **AI guardrails required** — LLM should not provide dangerous advice
3. **Audit trail mandatory** — All ticket creation must be logged
4. **Latency budget** — Operators on shift need quick responses (<5s)
5. **Cost control** — Gemini API calls add to operational expense

---

## Contact & Support

- **Project Lead**: GlobalLogic Engineering Team
- **Client Contact**: FactoryOps Manufacturing COO
- **Tech Slack**: #factoryops-ai

---

**Last Updated**: 2026-07-24  
**Version**: 1.0 (Planning Phase)
