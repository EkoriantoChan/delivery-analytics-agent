---
title: Delivery Analytics Agent
emoji: 📦
colorFrom: indigo
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
---

# Delivery Analytics Agent — Milestone Phase 2

An operational delivery analytics AI Agent built with **LangChain**, **FastAPI**, and modern LLMs (**OpenAI gpt-5.6-luna / gpt-4o-mini** and **Google Gemini**). Connected to a cloud **Neon PostgreSQL (Gold Schema)** database with multi-tenant conversation isolation in **SQLite** and AST SQL query guard using **SQLGlot**.

---

## 1. Key Capabilities & AI Framework

- **Agent Framework:** [LangChain](https://www.langchain.com/) (`langchain>=0.3.0`, `langchain-core>=0.3.0`) utilizing modular `@tool` decorated tools in [`src/tools.py`](src/tools.py).
- **Supported LLM Providers:**
  - **OpenAI:** `gpt-5.6-luna` (reasoning model with low reasoning effort) or `gpt-4o-mini`.
  - **Google Gemini:** `gemini-2.0-flash` / `gemini-1.5-flash` / `gemini-1.5-pro`.
- **Hybrid Text-to-SQL + ChromaDB RAG:** Integrates local vector search via **ChromaDB** (`src/rag.py`) over contractual carrier SLA agreements (`docs/policies/carrier_sla_agreements.md`). Enables pure policy questions and hybrid compliance audits (evaluating actual SQL metrics against contractual on-time thresholds and refund rules).
- **Dynamic Multilingual Support:** The agent automatically detects the language used by the user in the prompt (e.g., English or Indonesian) and provides complete answers, data basis descriptions, and error/refusal messages in the matching language.
- **SQL Security Guard:** AST validation via **SQLGlot** enforcing single-statement read-only `SELECT` queries on allowlisted `gold.*` tables with automatic `LIMIT 100` and 5-second statement timeout.
- **Strict Tenant & IDOR Protection:** Multi-tenant conversation isolation where unauthorized cross-user access attempts return `HTTP 404 Not Found`.

---

## 2. Project Directory Structure

```text
Analytics-Agent/
├── Dockerfile                  # Multi-service Docker image (API & UI)
├── compose.yaml                # Orchestrates API (8000) and UI (8501) services
├── .dockerignore               # Excludes .env, virtual environments, cache, and SQLite
├── app.py                      # Interactive Streamlit UI with chart plotting, KPI cards & IDOR tester
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .env                        # Local runtime configuration
├── src/                        # Application backend modules:
│   ├── __init__.py
│   ├── config.py               # Pydantic Settings
│   ├── api.py                  # FastAPI REST API endpoints
│   ├── auth.py                 # Bearer Token verification & identity resolution
│   ├── conversations.py        # SQLite storage with strict IDOR prevention
│   ├── agent.py                # LangChain Agent, bilingual support, scope guard, synthesis
│   ├── tools.py                # LangChain @tool decorated analytics & RAG functions
│   ├── rag.py                  # ChromaDB persistent vector store & policy retriever
│   ├── sql_guard.py            # AST SQL Validator with SQLGlot
│   └── gold.py                 # Neon PostgreSQL client (Read-Only role, 5s timeout)
├── tests/                      # Automated test suite (34 tests passing):
│   ├── __init__.py
│   ├── test_sql_guard.py       # SQLGlot AST validation & mutation rejection
│   ├── test_auth_and_conversations.py # IDOR & tenant isolation tests
│   ├── test_tools.py           # LangChain BaseTool contract tests
│   ├── test_rag.py             # ChromaDB chunking, semantic search & routing tests
│   ├── test_agent_language.py  # Dynamic English/Indonesian response tests
│   └── test_api.py             # FastAPI integration & security lifecycle tests
├── docs/                       # Project documentation:
│   ├── architecture.md         # Data flow, trust boundaries & RAG architecture diagram
│   ├── evaluation.md           # 14 evaluation test cases (expected vs actual)
│   ├── demo.md                 # 5–7 minute demonstration script
│   └── policies/               # Operational policies & contractual SLA documents:
│       └── carrier_sla_agreements.md # Carrier SLA targets, refund clauses, sanctions
├── evidence/
│   └── test-output.txt         # Sanitized test execution output (34 tests passing)
└── submission-checklist.md     # Verification checklist for project submission
```

---

## 3. Environment Configuration (.env)

Copy `.env.example` to `.env` and fill in the required configuration values:

```bash
cp .env.example .env
```

Example `.env` configuration:
```ini
# Backend API Endpoint for Streamlit UI
AGENT_API_URL=http://localhost:8000

# Neon Gold Database URL (Read-Only credentials)
GOLD_DATABASE_URL=postgresql://user:password@ep-placeholder.neon.tech/neondb?sslmode=require

# LLM Provider Configuration ("openai" or "gemini")
LLM_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.6-luna

# Google Gemini Configuration (if using Gemini)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Multi-Tenant Demo Tokens
DEMO_TOKEN_A=token-alice-demo-secret-123
DEMO_TOKEN_B=token-bob-demo-secret-456

# Local SQLite Storage Path
SQLITE_PATH=/app/data/conversations.sqlite3
```

---

## 4. Running the Application

### Method 1: Using Docker Compose (Recommended)

Ensure Docker Desktop is running, then execute:

**Windows PowerShell & macOS/Linux:**
```bash
# Build and start both API and UI containers
docker compose up --build
```

Once running:
- **Streamlit Web UI:** Open [http://localhost:8501](http://localhost:8501) in your browser.
- **API Healthcheck:** Visit [http://localhost:8000/healthz](http://localhost:8000/healthz) (returns `{"status":"ok"}`).
- **API Swagger Documentation:** Visit [http://localhost:8000/docs](http://localhost:8000/docs).

To stop the containers:
```bash
docker compose down
```
*(Note: Avoid using the `-v` flag so the persistent SQLite conversation volume is preserved across restarts).*

---

### Method 2: Running Locally (Without Docker)

#### On Windows PowerShell:
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Configure local SQLite path
$env:SQLITE_PATH = "./data/conversations.sqlite3"

# 4. Start Backend API (Terminal 1)
uvicorn src.api:app --host 0.0.0.0 --port 8000

# 5. Start Streamlit UI (Terminal 2)
$env:AGENT_API_URL = "http://localhost:8000"
streamlit run app.py --server.port 8501
```

#### On macOS/Linux:
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
python3 -m pip install -r requirements.txt

# 3. Configure local SQLite path
export SQLITE_PATH="./data/conversations.sqlite3"

# 4. Start Backend API (Terminal 1)
uvicorn src.api:app --host 0.0.0.0 --port 8000

# 5. Start Streamlit UI (Terminal 2)
export AGENT_API_URL="http://localhost:8000"
streamlit run app.py --server.port 8501
```

---

## 5. Running Automated Tests

Run the complete test suite to verify hard gate compliance (AST SQL Guard, IDOR authorization, LangChain tools, dynamic bilingual responses, and API lifecycle):

```bash
python -m pytest tests/ -v
```

The test suite validates:
1. `tests/test_sql_guard.py`: 100% blocking of data mutations (`UPDATE`, `INSERT`, `DELETE`, `DROP`, `ALTER`), multi-statement `;`, forbidden schemas, and dangerous functions.
2. `tests/test_auth_and_conversations.py`: Prevention of IDOR vulnerabilities (User B accessing User A's conversation returns `404 Not Found`).
3. `tests/test_tools.py`: LangChain `@tool` contract compliance and invocation testing.
4. `tests/test_agent_language.py`: Accurate detection and dynamic responses in English and Indonesian.
5. `tests/test_api.py`: FastAPI endpoints, conversation lifecycle, and prompt injection defense.

---

## 6. Current Limitations & Production Roadmap

This system is built as a secure operational delivery analytics agent. For enterprise-scale production deployment, the following upgrades are recommended:

1. **Enterprise Identity Provider (SSO / OIDC):**
   - *Current:* Fixed server-verified demo Bearer tokens.
   - *Production:* Integrate with an enterprise Identity Provider (e.g., Okta, Keycloak, or AWS Cognito) using RS256-signed JSON Web Tokens (JWT) with automatic key rotation and RBAC.
2. **Distributed Conversation Store:**
   - *Current:* SQLite stored in a persistent Docker named volume.
   - *Production:* Migrate to a managed PostgreSQL cluster with Row-Level Security (RLS) and automatic data retention policies.
3. **Connection Pooling & Query Caching:**
   - *Current:* Per-query client connection with 5-second statement timeout.
   - *Production:* Deploy PgBouncer in front of Neon and introduce Redis caching for immutable historical daily aggregation metrics.
4. **Observability & Audit Tracing:**
   - *Current:* Standard console logging.
   - *Production:* Integrate OpenTelemetry with LangSmith or Langfuse for tracing LLM latency, token usage, and end-to-end execution audit logs.
