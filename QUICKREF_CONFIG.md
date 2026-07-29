# FactoryOps AI - Configuration Quick Reference

## Three Ways to Configure

### Option 1: Local Development (Recommended)
```bash
cp pyproject.local.example.toml pyproject.local.toml
# Edit pyproject.local.toml and add your API key
```

### Option 2: Environment Variables
```bash
export GOOGLE_API_KEY="your-key"
export APP_ENV="production"
export LANGSMITH_API_KEY="your-key"
```

### Option 3: Streamlit Cloud
- Go to **App Settings → Secrets**
- Paste from `.streamlit/secrets.example.toml`
- Update values
- Save → automatic reload

---

## File Quick Reference

| File | Committed? | Secrets? | Purpose |
|------|:----------:|:--------:|---------|
| `pyproject.toml` | ✅ Yes | ❌ No | Defaults & structure |
| `pyproject.local.toml` | ❌ No | ✅ Yes | Your local API keys |
| `pyproject.example.toml` | ✅ Yes | ❌ No | Example/template |
| `pyproject.local.example.toml` | ✅ Yes | ❌ No | Template for local |
| `.streamlit/secrets.toml` | ❌ No | ✅ Yes | Cloud secrets (managed by Streamlit) |
| `.streamlit/secrets.example.toml` | ✅ Yes | ❌ No | Template for cloud |

---

## Get API Keys

| Service | Where | How |
|---------|-------|-----|
| **Gemini** | https://aistudio.google.com/apikey | Click "Create API Key" |
| **LangSmith** | https://smith.langchain.com | Sign up → Settings → API key |

---

## Config Priority (Highest to Lowest)

```
1. Environment Variable         export GOOGLE_API_KEY=...
2. pyproject.local.toml         [tool.factoryops.api] google-api-key = ...
3. pyproject.toml              [tool.factoryops.api] google-api-key = ...
4. Python default              class Settings: google_api_key = ""
```

---

## Environment Variable Names

| TOML Key | Env Var |
|----------|---------|
| `[tool.factoryops.api]` `google-api-key` | `GOOGLE_API_KEY` |
| `[tool.factoryops.app]` `env` | `APP_ENV` |
| `[tool.factoryops.llm]` `model-name` | `MODEL_NAME` |
| `[tool.factoryops.langsmith]` `api-key` | `LANGSMITH_API_KEY` |
| `[tool.factoryops.langsmith]` `batch-timeout-ms` | `LANGSMITH_BATCH_TIMEOUT_MS` |

**Pattern:** Replace `-` with `_`, convert to UPPERCASE

---

## All Configuration Options

### API & LLM
```toml
[tool.factoryops.api]
google-api-key = ""           # Required: Gemini API key
timeout-seconds = 30          # API timeout
max-retries = 3               # Retry failed requests

[tool.factoryops.llm]
model-name = "gemini-1.5-flash"
temperature = 0.7             # Creativity level 0.0-1.0
max-tokens = 2048             # Max response length
```

### App & Security
```toml
[tool.factoryops.app]
name = "FactoryOps AI"
env = "development"           # development|staging|production
log-level = "INFO"            # DEBUG|INFO|WARNING|ERROR

[tool.factoryops.security]
session-timeout-minutes = 30
```

### Agent & Memory
```toml
[tool.factoryops.agent]
max-iterations = 10           # Max tool calls per request
timeout-seconds = 30.0

[tool.factoryops.memory]
max-conversation-length = 100
conversation-buffer-type = "buffer"
```

### Database & APIs
```toml
[tool.factoryops.database]
url = "sqlite:///./data/factory_ops.db"
# Production: postgresql://user:pass@host/db

[tool.factoryops.integrations]
mes-api-url = "http://..."
maintenance-api-url = "http://..."
inventory-api-url = "http://..."
```

### Data & Monitoring
```toml
[tool.factoryops.data]
machines-data-path = "src/data/machines.json"
error-codes-data-path = "src/data/error_codes.json"
technicians-data-path = "src/data/technicians.json"
tickets-data-path = "src/data/maintenance_tickets.json"

[tool.factoryops.monitoring]
enable-logging = true
log-file = "logs/factoryops.log"

[tool.factoryops.langsmith]
api-key = ""                  # Optional: for tracing
project = "Factory"
tracing = true
```

---

## Use in Code

```python
from src.config import settings

# Access any setting
print(settings.google_api_key)        # Your API key
print(settings.app_name)              # "FactoryOps AI"
print(settings.database_url)          # sqlite:///...
print(settings.model_name)            # "gemini-1.5-flash"
print(settings.langsmith_api_key)     # Your LangSmith key
```

---

## Troubleshooting

### Key not found
```bash
export GOOGLE_API_KEY="your-key"
streamlit run src/ui/streamlit_app.py
```

### Check which value is being used
```bash
LOG_LEVEL=DEBUG streamlit run src/ui/streamlit_app.py
# Look for: "✓ Configuration loaded" in output
```

### Verify TOML syntax
```bash
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
# No error = valid
```

---

## Production Checklist

- [ ] `pyproject.toml` has NO secrets
- [ ] `pyproject.local.toml` is gitignored
- [ ] `.streamlit/secrets.toml` is gitignored
- [ ] Secrets set in cloud (Streamlit Cloud / env vars / secret manager)
- [ ] `DATABASE_URL` uses PostgreSQL (not SQLite)
- [ ] `APP_ENV=production`
- [ ] `LOG_LEVEL=INFO`
- [ ] `LANGSMITH_TRACING=true` (for monitoring)

---

## Quick Commands

```bash
# Create local config
cp pyproject.local.example.toml pyproject.local.toml

# Test config loads
python -c "from src.config import settings; print(settings)"

# Run app
streamlit run src/ui/streamlit_app.py

# Check Streamlit secrets syntax
python -c "import tomllib; tomllib.load(open('.streamlit/secrets.example.toml', 'rb'))"

# Override env var
export GOOGLE_API_KEY="new-key" && streamlit run src/ui/streamlit_app.py

# Set multiple env vars
export GOOGLE_API_KEY="key" && \
export APP_ENV="production" && \
export LOG_LEVEL="INFO" && \
streamlit run src/ui/streamlit_app.py
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| **CONFIG_README.md** | Detailed configuration guide |
| **DEPLOYMENT.md** | Deployment strategies |
| **TOML_MIGRATION_SUMMARY.md** | What changed & why |
| **This file** | Quick reference |

---

**Need more details?** See [CONFIG_README.md](CONFIG_README.md)
