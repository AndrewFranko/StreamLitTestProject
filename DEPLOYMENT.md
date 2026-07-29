# FactoryOps AI - Deployment Guide

## Configuration Strategy

FactoryOps AI uses a **three-tier configuration system** optimized for Streamlit Cloud and enterprise deployment:

1. **pyproject.toml** — Defaults and public config (committed to git)
2. **pyproject.local.toml** — Local development secrets (gitignored)
3. **Environment Variables** — Runtime overrides (highest priority)

### Priority Order
```
Environment Variables > pyproject.local.toml > pyproject.toml > Defaults
```

---

## Local Development Setup

### 1. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create Local Secrets File
```bash
cp pyproject.local.example.toml pyproject.local.toml
```

### 3. Add Your API Keys
Edit `pyproject.local.toml`:
```toml
[tool.factoryops.api]
google-api-key = "your-gemini-api-key-from-aistudio-google-com"

[tool.factoryops.langsmith]
api-key = "your-langsmith-key-from-smith-langchain-com"
```

### 4. Run Locally
```bash
streamlit run src/ui/streamlit_app.py
```

---

## Streamlit Cloud Deployment

### 1. Connect Your Repository
- Push code to GitHub (with `pyproject.toml` and default config)
- Connect repo to Streamlit Cloud: https://share.streamlit.io/

### 2. Configure Secrets in Streamlit Cloud

Go to **App Settings → Secrets** and copy the entire contents of `.streamlit/secrets.example.toml`, then:

```toml
# Paste this into Streamlit Cloud "Secrets" section

[tool.factoryops.api]
google-api-key = "your-actual-gemini-api-key"

[tool.factoryops.langsmith]
api-key = "your-actual-langsmith-api-key"

# ... rest of configuration
```

### 3. How It Works
- Streamlit Cloud reads from `.streamlit/secrets.toml` (not in git)
- Your app loads `pyproject.toml` → reads `.streamlit/secrets.toml` as env vars → uses them
- Secrets are never exposed in logs or source code

---

## Configuration via Environment Variables

All config values can be set as environment variables (useful for Docker, Kubernetes, CI/CD):

```bash
# Gemini API
export GOOGLE_API_KEY="sk-..."

# App Settings
export APP_ENV="production"
export LOG_LEVEL="INFO"

# LLM Configuration
export MODEL_NAME="gemini-1.5-flash"
export TEMPERATURE="0.7"
export MAX_TOKENS="2048"

# Database
export DATABASE_URL="postgresql://user:pass@host/db"

# LangSmith
export LANGSMITH_API_KEY="lsv2_..."
export LANGSMITH_PROJECT="Factory"
export LANGSMITH_TRACING="true"
```

---

## Docker Deployment

### Dockerfile Example
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "src/ui/streamlit_app.py"]
```

### Docker Compose with Environment
```yaml
services:
  factoryops:
    build: .
    ports:
      - "8501:8501"
    environment:
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      DATABASE_URL: postgresql://postgres:${DB_PASS}@db:5432/factory_ops
      APP_ENV: production
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${DB_PASS}
      POSTGRES_DB: factory_ops
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

Run with:
```bash
export GOOGLE_API_KEY="your-key"
export DB_PASS="secure-password"
docker-compose up
```

---

## Production Best Practices

### 1. Use Cloud Secret Management
- **AWS**: AWS Secrets Manager, SSM Parameter Store
- **GCP**: Google Secret Manager
- **Azure**: Azure Key Vault
- **Kubernetes**: Sealed Secrets, External Secrets Operator

Example with AWS Secrets Manager:
```python
import json
import boto3

def load_secrets():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    secret = client.get_secret_value(SecretId='factoryops/production')
    return json.loads(secret['SecretString'])

secrets = load_secrets()
os.environ['GOOGLE_API_KEY'] = secrets['google_api_key']
```

### 2. Database Configuration
For production, **do not use SQLite**. Use PostgreSQL or managed services:

```toml
# pyproject.toml (development)
[tool.factoryops.database]
url = "sqlite:///./data/factory_ops.db"

# Environment (production)
DATABASE_URL="postgresql://user:pass@managed-db.cloud.example.com/factory_ops"
```

### 3. Enable Logging & Monitoring
```bash
APP_ENV=production
LOG_LEVEL=INFO
ENABLE_LOGGING=true
LOG_FILE=/var/log/factoryops.log

# LangSmith Tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=Factory
```

### 4. Secure API Keys
- **Never hardcode** API keys in source code
- **Never commit** `.env` or `pyproject.local.toml`
- **Always use** encrypted secret management
- **Rotate keys** periodically
- **Monitor** API usage for anomalies

Verify `.gitignore` includes:
```
.env
.env.local
pyproject.local.toml
.streamlit/secrets.toml
logs/
data/
```

### 5. Environment-Specific Config
```bash
# Development
APP_ENV=development
LANGSMITH_TRACING=true  # Monitor locally

# Staging
APP_ENV=staging
DATABASE_URL=postgresql://...staging...

# Production
APP_ENV=production
LANGSMITH_TRACING=true  # Monitor in prod
LOG_LEVEL=INFO
ENABLE_LOGGING=true
```

---

## Configuration File Reference

### pyproject.toml Structure
```toml
[tool.factoryops.api]
google-api-key = ""  # Can be empty - will use env var
timeout-seconds = 30

[tool.factoryops.app]
env = "development"
name = "FactoryOps AI"
log-level = "INFO"

[tool.factoryops.llm]
model-name = "gemini-1.5-flash"
temperature = 0.7
max-tokens = 2048

[tool.factoryops.data]
machines-data-path = "src/data/machines.json"
error-codes-data-path = "src/data/error_codes.json"

[tool.factoryops.database]
url = "sqlite:///./data/factory_ops.db"

[tool.factoryops.langsmith]
api-key = ""
project = "Factory"
endpoint = "https://eu.api.smith.langchain.com"
```

### Load Priority
```
1. Environment Variable (e.g., GOOGLE_API_KEY=...)
2. pyproject.local.toml value
3. pyproject.toml value
4. Python default in Settings class
```

Example: If you set both in pyproject.toml and env:
```bash
# pyproject.toml
[tool.factoryops.app]
env = "development"

# Terminal
export APP_ENV=production

# Result: app_env = "production" (env var wins)
```

---

## Troubleshooting

### "GOOGLE_API_KEY is required"
✓ Check 1: Set in environment variable
```bash
export GOOGLE_API_KEY="your-key"
```

✓ Check 2: Add to pyproject.local.toml
```toml
[tool.factoryops.api]
google-api-key = "your-key"
```

✓ Check 3: For Streamlit Cloud, add to Secrets section

### Config not loading
Enable debug logging:
```bash
LOG_LEVEL=DEBUG
```

Check logs for:
```
✓ Configuration loaded: FactoryOps AI (development)
✓ Merged local config from /path/to/pyproject.local.toml
```

### Streamlit Cloud deployment fails
1. Verify `requirements.txt` is up-to-date:
```bash
pip freeze > requirements.txt
```

2. Check `.gitignore` doesn't exclude `pyproject.toml`:
```bash
git ls-files | grep pyproject.toml
```

3. Verify secrets in Streamlit Cloud Settings match your app's expectations

---

## Quick Reference

| Environment | Config Source | Secrets | DB |
|---|---|---|---|
| **Local Dev** | pyproject.toml + pyproject.local.toml | .env, pyproject.local.toml | SQLite |
| **Streamlit Cloud** | pyproject.toml + .streamlit/secrets.toml | Streamlit Secrets panel | SQLite (or cloud) |
| **Docker** | pyproject.toml + environment | docker-compose.yml, .env | Depends on config |
| **Kubernetes** | ConfigMap + Secrets | Secret resource | Cloud DB |
| **AWS/GCP** | pyproject.toml | Secrets Manager | RDS/CloudSQL |

---

**Last Updated**: 2026-07-29  
**Version**: 1.0
