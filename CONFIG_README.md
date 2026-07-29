# FactoryOps AI - Configuration Guide

## Overview

All environment values are now stored in **TOML format** in `pyproject.toml` for easy Streamlit Cloud deployment.

### Configuration Hierarchy

```
Environment Variables (highest priority)
    ↓
pyproject.local.toml (local secrets - gitignored)
    ↓
pyproject.toml (defaults - committed to git)
    ↓
Python defaults (lowest priority)
```

---

## Quick Start

### Local Development

1. **Copy template to local secrets:**
   ```bash
   cp pyproject.local.example.toml pyproject.local.toml
   ```

2. **Add your Gemini API key:**
   ```toml
   # pyproject.local.toml
   [tool.factoryops.api]
   google-api-key = "your-gemini-api-key-here"
   ```

3. **Run the app:**
   ```bash
   streamlit run src/ui/streamlit_app.py
   ```

### Streamlit Cloud Deployment

1. **Push to GitHub** (with `pyproject.toml`, `.gitignore` includes `pyproject.local.toml`)

2. **Go to Streamlit Cloud → Secrets**

3. **Copy `.streamlit/secrets.example.toml` and update values:**
   ```toml
   [tool.factoryops.api]
   google-api-key = "your-actual-key"
   
   [tool.factoryops.langsmith]
   api-key = "your-actual-key"
   ```

4. **Done!** Streamlit Cloud automatically loads `secrets.toml` as environment variables.

---

## Configuration Files

### `pyproject.toml` — Public Config (Committed)
- Default values and structure
- NO secrets - empty values for API keys
- Used in production with Streamlit Cloud/environment variables

**Example:**
```toml
[tool.factoryops.api]
google-api-key = ""  # Empty - will use env var or pyproject.local.toml
timeout-seconds = 30

[tool.factoryops.app]
env = "development"
name = "FactoryOps AI"
```

### `pyproject.local.toml` — Local Secrets (Gitignored)
- Your actual API keys
- Only for local development
- Never committed to git

**Example:**
```toml
[tool.factoryops.api]
google-api-key = "AIzaSyD..."

[tool.factoryops.langsmith]
api-key = "lsv2_pt_..."
```

### `.streamlit/secrets.toml` — Cloud Secrets (Managed by Streamlit)
- Set via Streamlit Cloud UI
- Never in git
- Automatically available as environment variables

---

## All Configuration Options

### API Configuration
```toml
[tool.factoryops.api]
google-api-key = ""          # Gemini API key
timeout-seconds = 30         # API call timeout
max-retries = 3              # Retry failed calls
```

### App Settings
```toml
[tool.factoryops.app]
name = "FactoryOps AI"       # App display name
env = "development"          # development|staging|production
log-level = "INFO"           # DEBUG|INFO|WARNING|ERROR
```

### LLM Configuration
```toml
[tool.factoryops.llm]
model-name = "gemini-1.5-flash"  # Model to use
temperature = 0.7                # Creativity (0.0-1.0)
max-tokens = 2048                # Response length limit
```

### Memory & Agent Settings
```toml
[tool.factoryops.memory]
max-conversation-length = 100
conversation-buffer-type = "buffer"

[tool.factoryops.agent]
max-iterations = 10           # Max tool calls per request
timeout-seconds = 30.0        # Agent timeout
```

### Data Paths
```toml
[tool.factoryops.data]
machines-data-path = "src/data/machines.json"
error-codes-data-path = "src/data/error_codes.json"
technicians-data-path = "src/data/technicians.json"
tickets-data-path = "src/data/maintenance_tickets.json"
```

### Database
```toml
[tool.factoryops.database]
url = "sqlite:///./data/factory_ops.db"
# Production: "postgresql://user:pass@host/db"
```

### API Integration Endpoints
```toml
[tool.factoryops.integrations]
mes-api-url = "http://mes-internal.factoryops.com/api"
maintenance-api-url = "http://maintenance.factoryops.com/api"
inventory-api-url = "http://inventory.factoryops.com/api"
```

### Monitoring & Logging
```toml
[tool.factoryops.monitoring]
enable-logging = true
log-file = "logs/factoryops.log"
```

### LangSmith Configuration
```toml
[tool.factoryops.langsmith]
api-key = ""                              # LangSmith API key
project = "Factory"                       # Project name
endpoint = "https://eu.api.smith.langchain.com"
batch-timeout-ms = 100
timeout-ms = 10000
tracing-v2 = true                         # Enable tracing v2
tracing = true                            # Enable tracing
callbacks-background = false              # Sync callbacks
```

---

## Environment Variable Override

Any config value can be set via environment variable (takes highest priority):

```bash
# Override via env vars
export GOOGLE_API_KEY="your-key"
export APP_ENV="production"
export MODEL_NAME="gemini-1.5-pro"
export LANGSMITH_TRACING="true"

# Run app
streamlit run src/ui/streamlit_app.py
```

**Env var name = section + key in UPPER_SNAKE_CASE:**
```
[tool.factoryops.api]
google-api-key      →  GOOGLE_API_KEY
timeout-seconds     →  TIMEOUT_SECONDS

[tool.factoryops.llm]
model-name          →  MODEL_NAME
max-tokens          →  MAX_TOKENS

[tool.factoryops.langsmith]
api-key             →  LANGSMITH_API_KEY
batch-timeout-ms    →  LANGSMITH_BATCH_TIMEOUT_MS
```

---

## How Config is Loaded

1. **Read `pyproject.toml`** → Get defaults
2. **Read `pyproject.local.toml`** (if exists) → Merge & override
3. **Read environment variables** → Final override
4. **Pydantic `Settings` class** → Validate & use

### In Code

```python
from src.config import settings

# Access any config value:
print(settings.app_name)              # "FactoryOps AI"
print(settings.google_api_key)        # "AIzaSy..."
print(settings.database_url)          # "sqlite:///..."
print(settings.model_name)            # "gemini-1.5-flash"
```

---

## Troubleshooting

### "GOOGLE_API_KEY is required"

**Solution 1: Set environment variable**
```bash
export GOOGLE_API_KEY="your-api-key"
```

**Solution 2: Add to pyproject.local.toml**
```toml
[tool.factoryops.api]
google-api-key = "your-api-key"
```

**Solution 3: For Streamlit Cloud**
- Go to **App Settings → Secrets**
- Add: `GOOGLE_API_KEY = "your-api-key"`

### Config not being read

**Check 1: Enable debug logging**
```bash
export LOG_LEVEL=DEBUG
streamlit run src/ui/streamlit_app.py
```

**Check 2: Verify files exist**
```bash
ls pyproject.toml
ls pyproject.local.toml  # optional, only for local dev
```

**Check 3: Check file syntax**
```bash
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
# No errors = valid TOML
```

### Value not changing

Remember the priority order:
```
ENV VAR > pyproject.local.toml > pyproject.toml > Default
```

If a value is in `pyproject.toml`, you must override it via:
- Environment variable (recommended for cloud), OR
- `pyproject.local.toml` (local dev only)

---

## Getting API Keys

### Gemini API
1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy the key
4. Add to config

### LangSmith (Optional - for tracing)
1. Go to https://smith.langchain.com/
2. Sign up / Log in
3. Create a new project
4. Get API key from settings
5. Add to config

---

## Production Checklist

- [ ] `pyproject.toml` contains defaults only (no secrets)
- [ ] `pyproject.local.toml` is in `.gitignore`
- [ ] `.env` is in `.gitignore`
- [ ] `.streamlit/secrets.toml` is in `.gitignore`
- [ ] Secrets are set via Streamlit Cloud UI or environment variables
- [ ] Database URL is production-ready (PostgreSQL, not SQLite)
- [ ] `LOG_LEVEL` is `INFO` (not `DEBUG`)
- [ ] `APP_ENV` is `production`
- [ ] LangSmith tracing is enabled for monitoring
- [ ] All API endpoints are configured for production

---

**Questions?** See [DEPLOYMENT.md](DEPLOYMENT.md) for more details.
