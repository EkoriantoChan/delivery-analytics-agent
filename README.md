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

> 📽️ **Project Presentation Slides:**
> - **Google Slides:** [Delivery Analytics Agent Presentation](https://docs.google.com/presentation/d/1sYFwctYx0lv6_Kvsk9pDkdLyw73q-Nz4)
> - **Local Slide Deck:** [`Delivery_Analytics_Agent_Presentation.pptx`](Delivery_Analytics_Agent_Presentation.pptx)

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
├── tests/                      # Automated test suite (37 tests passing):
│   ├── __init__.py
│   ├── test_sql_guard.py       # SQLGlot AST validation & mutation rejection
│   ├── test_auth_and_conversations.py # IDOR & tenant isolation tests
│   ├── test_tools.py           # LangChain BaseTool contract tests
│   ├── test_rag.py             # ChromaDB chunking, semantic search & routing tests
│   ├── test_agent_language.py  # Dynamic English/Indonesian response tests
│   ├── test_edge_cases.py      # Benchmark edge cases & mutation guard tests
│   └── test_api.py             # FastAPI integration & security lifecycle tests
├── pytest.ini                  # Pytest configuration restricting testpaths to tests/
├── docs/                       # Project documentation:
│   ├── architecture.md         # Data flow, trust boundaries & RAG architecture diagram
│   ├── evaluation.md           # 14 evaluation test cases (expected vs actual)
│   ├── demo.md                 # 5–7 minute demonstration script
│   └── policies/               # Operational policies & contractual SLA documents:
│       └── carrier_sla_agreements.md # Carrier SLA targets, refund clauses, sanctions
├── Delivery_Analytics_Agent_Presentation.pptx # Project presentation slide deck
├── evidence/
│   └── test-output.txt         # Sanitized test execution output (37 tests passing)
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

Run the complete test suite to verify hard gate compliance (AST SQL Guard, IDOR authorization, LangChain tools, dynamic bilingual responses, edge cases, and API lifecycle):

```bash
# Run all 37 tests with verbose output
python -m pytest tests/ -v
```

The test suite validates:
1. `tests/test_sql_guard.py`: 100% blocking of data mutations (`UPDATE`, `INSERT`, `DELETE`, `DROP`, `ALTER`), multi-statement `;`, forbidden schemas, and dangerous functions.
2. `tests/test_auth_and_conversations.py`: Prevention of IDOR vulnerabilities (User B accessing User A's conversation returns `404 Not Found`).
3. `tests/test_tools.py`: LangChain `@tool` contract compliance and invocation testing.
4. `tests/test_agent_language.py`: Accurate detection and dynamic responses in English and Indonesian.
5. `tests/test_edge_cases.py`: Benchmark edge cases verification (`delivered_at_utc` timestamp filter, partial September boundary disclosure, and write mutation refusal).
6. `tests/test_rag.py`: ChromaDB semantic RAG retrieval, markdown policy chunking, and dual-engine query routing.
7. `tests/test_api.py`: FastAPI endpoints, conversation lifecycle, and prompt injection defense.

All 37 automated tests pass 100% with zero failures. Sanitized execution evidence is recorded in [`evidence/test-output.txt`](evidence/test-output.txt).

---

## 6. Cloud Deployment Guide (Free & Production Options)

This repository is containerized and ready to deploy across multiple cloud platforms:

### Option A: Hugging Face Spaces (Recommended — 100% Free, 24/7 Uptime, No Credit Card)
The repository is pre-configured with Hugging Face Space metadata in `README.md` (`sdk: docker`, `app_port: 7860`).
1. Go to [huggingface.co](https://huggingface.co/) and log in.
2. Click **New Space** $\rightarrow$ Enter space name (e.g. `delivery-analytics-agent`).
3. Select **Docker** $\rightarrow$ **Blank**.
4. Choose License (e.g. `MIT`) $\rightarrow$ Click **Create Space**.
5. Connect your GitHub repository (`EkoriantoChan/delivery-analytics-agent`) or push code to the Space's Git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/delivery-analytics-agent
   git push space main
   ```
6. Navigate to **Settings $\rightarrow$ Variables and secrets** in your Space, and add:
   - `GOLD_DATABASE_URL`: Your read-only Neon connection string
   - `OPENAI_API_KEY` (or `GEMINI_API_KEY`): Your LLM API key
   - `LLM_PROVIDER`: `openai` or `gemini`
7. The Space will automatically build the `Dockerfile`, launch `start.sh`, and serve the app at a permanent free HTTPS URL.

### Option B: Render.com (Free Web Service via GitHub)
1. Sign up / Log in to [render.com](https://render.com/) with your GitHub account.
2. Click **New + $\rightarrow$ Web Service**.
3. Select your repository: `EkoriantoChan/delivery-analytics-agent`.
4. Name your service $\rightarrow$ Select Runtime: **Docker**.
5. Select the **Free** instance type (no credit card required).
6. Under **Environment Variables**, add the keys from your `.env` file (`GOLD_DATABASE_URL`, `OPENAI_API_KEY` / `GEMINI_API_KEY`, `LLM_PROVIDER`).
7. Click **Deploy Web Service**. Render builds the Docker image and publishes a public `*.onrender.com` URL.

### Option C: Cloudflare Tunnel (Instant Public HTTPS from Local Docker)
If you want to demo live directly from your machine without uploading container images:
1. Start the containers locally:
   ```bash
   docker compose up --build
   ```
2. In a separate terminal, launch a secure Cloudflare Tunnel:
   ```bash
   npx cloudflared tunnel --url http://localhost:8501
   ```
3. Cloudflare outputs a public HTTPS link (e.g. `https://random-name.trycloudflare.com`) accessible from any browser worldwide.

---

## 7. Current Limitations & Production Roadmap

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

---

## 8. Project Presentation & Slide Deck

- 🔗 **Google Slides:** [https://docs.google.com/presentation/d/1sYFwctYx0lv6_Kvsk9pDkdLyw73q-Nz4](https://docs.google.com/presentation/d/1sYFwctYx0lv6_Kvsk9pDkdLyw73q-Nz4)
- 📊 **Local Presentation File:** [`Delivery_Analytics_Agent_Presentation.pptx`](Delivery_Analytics_Agent_Presentation.pptx)

### Slide Deck Structure & Summary:
1. **Pendahuluan (Introduction):** Background on e-commerce logistics complexity, data pipeline latency, and the pitfalls of naive LLM chatbots (number fabrication, date dimension confusion, mutation risks).
2. **Solusi & Teknis (Architecture):** Layered zero-trust system architecture covering the Client UI/3D Twin, FastAPI authentication & IDOR shields, Gemini 2.5 Flash / OpenAI dual-engine, SQLGlot AST guard, and Neon Serverless PostgreSQL Gold schema.
3. **Solusi & Teknis (Workflow Flowchart):** Visual flowchart detailing prompt lifecycle, pre-LLM security shields (`check_prompt_injection`, `is_out_of_scope_or_mutation`), intent routing, ChromaDB semantic retrieval branch, and Text-to-SQL Neon execution branch.
4. **Solusi & Teknis (Tools & ChromaDB Registry):** Complete specifications and invocation triggers for all 3 tools:
   - `execute_gold_sql_query`: Read-only Neon PostgreSQL query execution with SQLGlot AST security.
   - `get_gold_schema_documentation`: Authoritative table and business metric definitions.
   - `search_logistics_policies_and_sla`: Semantic RAG powered by **ChromaDB** (`carrier_sla_policies` collection with MiniLM embeddings).
   - Zero Side-Effect Principle (prohibiting web search, database mutation, and server file access).
5. **Demonstrasi (Live Demo):** Grounded SQL analytics, multi-turn stateful follow-up, prompt injection & IDOR attack shields, and the interactive 3D Java logistics digital twin.
6. **Evaluasi (Benchmark Edge Cases Matrix):** Official 8-case benchmark matrix with evaluation status, criteria, and source code line anchors.
7. **Evaluasi (Deep Dive on Failures & Fixes):** Root cause analysis and code implementations for resolved edge cases (Case 2: Sept 1–30 boundary disclosure, Case 5: Express monetary refund ratio, Case 8: Delivered vs ordered timestamp filter) plus security guardrails (Cases 10 & 11).
8. **Evaluasi & Roadmap:** Production limitations and enterprise roadmap (SSO/OIDC, Kafka/Debezium real-time streaming, root-cause RAG, and OpenTelemetry distributed tracing).
