---
last_mapped_commit: cf96f4d0048d4bf12ec1ec9d2a683bd1077373a2
last_mapped_at: 2026-10-05
---
# Technology Stack

**Analysis Date:** 2026-10-05

## Languages

**Primary:**
- Python 3.11+ / 3.13 - All core application code (`src/`), ingestion pipelines, Signal Engine, AI Inference, and Streamlit presentation dashboard.

**Secondary:**
- SQL (PostgreSQL dialect) - Database migrations and schema definitions (`src/database/schemas.sql`).
- Markdown & JSON - Knowledge rules (`knowledge/*.okf.md`) and declarative market constituent registry (`knowledge/*.okf.json`, `src/config/*.json`).
- YAML - Continuous integration, container deployment, and automation cron workflows (`.github/workflows/*.yml`).
- Dockerfile - Container specifications for UI and ingestion services (`docker/*.Dockerfile`).

## Runtime

**Environment:**
- Python 3.11+ (CPython, tested with 3.13)
- Multi-environment operational deployment:
  - Local / Developer workstation
  - GitHub Actions scheduled runners (Cron pipeline every 2 hours, OKF updater, DB maintenance)
  - Streamlit Cloud / Docker container for presentation layer (`src/ui/app.py`)
  - Modal serverless container deployment (`src/ai_engine/modal_app.py`) for custom Contrastive-LM (CLM) inference
  - Hugging Face Spaces alternative container runtime (`src/ai_engine/hf_space/`, `src/hf_space/`)

**Package Manager:**
- pip
- Standard requirements specification: `requirements.txt` present

## Frameworks

**Core:**
- Streamlit >= 1.30.0 (running 1.65.0) - Reactive real-time quantitative dashboard and visualization frontend (`src/ui/app.py`).
- Plotly >= 5.18.0 - High-performance interactive financial time-series chart rendering (`go.Figure`, `go.Scatter`).
- Asyncio & aiohttp >= 3.11.12 - High-throughput asynchronous feed ingestion and concurrent network I/O (`src/ingestion/poller.py`).

**Testing:**
- Python standard library `unittest` - Unit testing suite across classifier, dedup, and OKF components (`tests/unit/`).

**AI & Machine Learning:**
- `typesafe-sdk` >= 0.7.2 - System-One CLM evaluation client interfacing with Modal endpoint.
- `google-genai` >= 2.0.0 - Dynamic Objective Knowledge Framework (OKF) macroeconomic updater.

## Key Dependencies

**Critical:**
- `typesafe-sdk` (>=0.7.2) - Client library communicating with Contrastive Language Model (CLM-8B) server on Modal for zero-hallucination probability projection `P(Bullish), P(Bearish), P(Neutral)`.
- `google-genai` (>=2.0.0) - Official Google GenAI SDK for updating macroeconomic rules via Gemini flash model fallbacks.
- `psycopg2-binary` (>=2.9.10) - PostgreSQL database driver managing Supabase connection pooling and data transactions.
- `pandas` (>=2.2.3) - Time-series manipulation, exponential moving averages (EMA), and tabular analysis.
- `feedparser` (>=6.0.0) - Multi-format RSS parsing across regional Google News and financial publishers.
- `alpaca-py` (>=0.40.0) - Order routing and execution integration for paper trading.

**Infrastructure:**
- `streamlit` - Institutional quantitative web terminal.
- `plotly` - Unified multi-index sentiment visualization.
- `requests` (>=2.31.0) - Synchronous HTTP dispatch and API health probing.

## Configuration

**Environment:**
- Managed via OS environment variables and `.env`:
  - `DATABASE_URL` - Supabase PostgreSQL connection string with session/transaction pooler.
  - `TYPESAFE_API_KEY` - API token for TypeSafe CLM serverless inference.
  - `GEMINI_API_KEY` - Google Gemini API key for automated OKF rule generation.
  - `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` - Credentials for Alpaca paper trading.

**Build & Config Files:**
- `.streamlit/config.toml` - Streamlit server and theme configurations.
- `src/config/market_registry.json` - Declarative configuration of regional markets, indices, tickers, and locales.
- `src/config/asset_classes.json` - Asset class criteria definitions.

## Platform Requirements

**Development:**
- Cross-platform: Windows, macOS, Linux supported.
- Devcontainer definition: `.devcontainer/devcontainer.json`.

**Production:**
- Database: Managed PostgreSQL (Supabase) with `uuid-ossp` extension and BRIN indexes.
- Dashboard: Streamlit Cloud / Docker container.
- AI Worker: Modal serverless GPU endpoint running CLM-8B.
- Ingestion & Cron: GitHub Actions scheduled workflows (`.github/workflows/ci.yml`, `update_okf.yml`).

---

*Stack analysis: 2026-10-05*
*Update after major dependency changes*
