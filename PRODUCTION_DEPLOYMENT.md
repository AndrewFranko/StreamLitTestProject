# FactoryOps AI - Production Deployment (Localhost)

## Quick Start

### Windows
```batch
run_production.bat
```

### Linux/Mac
```bash
chmod +x run_production.sh
./run_production.sh
```

---

## Prerequisites

- Python 3.10+
- pip package manager
- All API keys configured in `pyproject.local.toml`

---

## Configuration

### 1. Verify API Keys

Check `pyproject.local.toml` has:

```toml
[tool.factoryops.api]
api-key = "your-gemini-api-key"

[tool.factoryops.langsmith]
api-key = "your-langsmith-api-key"
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or using pyproject.toml:

```bash
pip install -e .
```

---

## Running the App

### Method 1: Using Run Scripts (Recommended)

**Windows:**
```batch
run_production.bat
```

**Linux/Mac:**
```bash
./run_production.sh
```

### Method 2: Manual Streamlit

```bash
streamlit run app.py --server.port 8501 --server.address localhost
```

### Method 3: Development Mode

```bash
streamlit run app.py  # Auto-reloads on code changes
```

---

## Access the Application

- **Web UI**: http://localhost:8501
- **Chat Interface**: http://localhost:8501/💬_Chat
- **Conversations**: http://localhost:8501/📊_Conversations
- **LangSmith Studio**: https://smith.langchain.com/studio?projectName=Factory

---

## What Gets Deployed

### Core Modules
- ✓ Agent Engine (LangChain + Gemini)
- ✓ Tool Calling (MCP Integration)
- ✓ Conversation Memory
- ✓ Guardrails Middleware
- ✓ LangSmith Tracing

### Features
- ✓ Multi-role support (Operator, Engineer, Supervisor, Plant Manager)
- ✓ Chat interface with history persistence
- ✓ Error code lookup
- ✓ Machine status checking
- ✓ Maintenance ticket creation
- ✓ Real-time LangSmith observability

### Files Deployed
```
app.py                              # Main entry point
pages/
  1_💬_Chat.py                      # Chat interface
  2_📊_Conversations.py             # Chat history
src/
  agent_engine.py                   # AI agent logic
  config.py                         # Configuration loading
  langsmith_config.py              # LangSmith integration
  tools.py                          # Tool definitions
  guardrails_middleware_layer.py   # Safety guardrails
  mcp_ticket_server.py             # Ticket creation
pyproject.toml                      # Project metadata
pyproject.local.toml               # Secrets (not committed)
requirements.txt                    # Dependencies
```

---

## Configuration Files

### pyproject.toml (Committed)
- Public configuration
- Default settings
- Project metadata
- LangSmith project name and endpoint

### pyproject.local.toml (Not Committed)
- API keys and secrets
- Keep this file PRIVATE
- Add to .gitignore

### .streamlit/secrets.example.toml
- Template for Streamlit Cloud deployment
- Copy to `.streamlit/secrets.toml` for Cloud

---

## Environment Variables

Override configuration with environment variables:

```bash
# Gemini API
export GOOGLE_API_KEY="sk-..."

# App Settings
export APP_ENV="production"
export LOG_LEVEL="INFO"

# Model Configuration
export MODEL_NAME="gemini-1.5-flash"
export TEMPERATURE="0.7"
export MAX_TOKENS="2048"

# LangSmith Tracing
export LANGSMITH_API_KEY="lsv2_..."
export LANGSMITH_PROJECT="Factory"
export LANGCHAIN_TRACING_V2="true"

# Database (optional)
export DATABASE_URL="sqlite:///./data/factory_ops.db"
```

---

## Monitoring

### LangSmith Observability

All queries are automatically traced to LangSmith Studio:

1. Go to: https://smith.langchain.com/studio?projectName=Factory
2. View all agent queries, tool calls, and responses
3. Monitor latency, errors, and token usage
4. Analyze patterns and improve prompts

### Application Logs

Logs are printed to console with timestamps:

```
[INFO] AgentEngine initialized - Role: operator, Model: gemini-1.5-flash
[DEBUG] Tool invoked: lookup_error_code
[INFO] LangSmith configured: project='Factory'
```

### Console Output

The run scripts show:
- Dependency installation status
- Configuration verification
- Server startup confirmation
- Application URL

---

## Troubleshooting

### 1. API Key Not Found

**Error:** `LANGSMITH_API_KEY not found`

**Fix:** Add to `pyproject.local.toml`:
```toml
[tool.factoryops.langsmith]
api-key = "lsv2_..."
```

### 2. Port Already in Use

**Error:** `Address already in use: ('127.0.0.1', 8501)`

**Fix:** Kill the existing process or use a different port:
```bash
streamlit run app.py --server.port 8502
```

### 3. Module Not Found

**Error:** `ModuleNotFoundError: No module named 'langchain'`

**Fix:** Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

### 4. LangSmith Not Tracing

**Error:** No traces appear in Studio

**Check:**
1. API key is set: `echo $LANGSMITH_API_KEY`
2. Tracing enabled: `LANGCHAIN_TRACING_V2=true`
3. Network connectivity to Smith endpoint

---

## Performance Tuning

### Response Latency

Default timeouts:
- LLM Call: 30 seconds
- Tool Call: 10 seconds
- Total Agent: 30 seconds

Adjust in `pyproject.toml`:
```toml
[tool.factoryops.api]
timeout-seconds = 60

[tool.factoryops.agent]
timeout-seconds = 60.0
```

### Memory Usage

Conversation history limited to 100 messages per session:
```toml
[tool.factoryops.memory]
max-conversation-length = 100
```

### Concurrent Users

Streamlit handles ~10-50 concurrent users per 2GB RAM instance.

---

## Scaling to Production

For multi-user production deployment:

1. **Database**: Migrate from SQLite to PostgreSQL
2. **Load Balancer**: Use nginx or AWS ALB
3. **Container**: Deploy with Docker
4. **Secrets Management**: Use AWS Secrets Manager or HashiCorp Vault
5. **Monitoring**: Add Prometheus/Datadog metrics
6. **Logging**: Send to CloudWatch or ELK stack

---

## Security Checklist

- ✓ API keys in `pyproject.local.toml` (gitignored)
- ✓ HTTPS required in production
- ✓ Rate limiting configured
- ✓ Input validation on all user queries
- ✓ LangSmith tracing for audit trail
- ✓ No sensitive data in logs

---

## Support

For issues:

1. Check logs in console output
2. Verify configuration in `pyproject.local.toml`
3. Test connectivity to Gemini API and LangSmith
4. Review LangSmith Studio for query traces

---

## Documentation

- **Architecture**: See [CLAUDE.md](CLAUDE.md)
- **Configuration**: See [CONFIG_README.md](CONFIG_README.md)
- **API Reference**: See [QUICKREF_CONFIG.md](QUICKREF_CONFIG.md)
- **Troubleshooting**: See [SYSTEM_STATUS.md](SYSTEM_STATUS.md)

---

**Version**: 1.0  
**Last Updated**: 2026-07-29  
**Status**: Production Ready
