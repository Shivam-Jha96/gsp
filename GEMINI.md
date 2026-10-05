<!-- GSD:project-start source:PROJECT.md -->

## Project

**Global Sentiment Platform of Share Markets (GSP)**

Global Sentiment Platform of Share Markets (GSP) is an institutional-grade quantitative macroeconomic sentiment and directional signal engine. It ingests global financial news, filters regional affinity and noise via compiled regex classifiers and fingerprint deduplication, generates continuous directional sentiment scores using serverless Contrastive Language Models (CLM-8B System-One), and presents live multi-index surfaces on a permanently dark-themed reactive Streamlit dashboard.

**Core Value:** Zero-hallucination, deterministic macroeconomic directional sentiment projection grounded in regional Objective Knowledge Framework (OKF) rules, coupled with ultra-low latency interactive multi-market visualization.

### Constraints

- **Theme**: Always in permanent dark mode (`#020617` background, `#0f172a` cards, `#10b981` / `#ef4444` directional accents).
- **API Quotas**: Strict compliance with Google Gemini free-tier 15 RPM quota (pacing interval >= 6.0s).
- **Latency**: Sub-second UI updates via `@st.fragment` isolation without full-page reloads.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.11+ / 3.13 - All core application code (`src/`), ingestion pipelines, Signal Engine, AI Inference, and Streamlit presentation dashboard.
- SQL (PostgreSQL dialect) - Database migrations and schema definitions (`src/database/schemas.sql`).
- Markdown & JSON - Knowledge rules (`knowledge/*.okf.md`) and declarative market constituent registry (`knowledge/*.okf.json`, `src/config/*.json`).
- YAML - Continuous integration, container deployment, and automation cron workflows (`.github/workflows/*.yml`).
- Dockerfile - Container specifications for UI and ingestion services (`docker/*.Dockerfile`).

## Runtime

- Python 3.11+ (CPython, tested with 3.13)
- Multi-environment operational deployment:
- pip
- Standard requirements specification: `requirements.txt` present

## Frameworks

- Streamlit >= 1.30.0 (running 1.65.0) - Reactive real-time quantitative dashboard and visualization frontend (`src/ui/app.py`).
- Plotly >= 5.18.0 - High-performance interactive financial time-series chart rendering (`go.Figure`, `go.Scatter`).
- Asyncio & aiohttp >= 3.11.12 - High-throughput asynchronous feed ingestion and concurrent network I/O (`src/ingestion/poller.py`).
- Python standard library `unittest` - Unit testing suite across classifier, dedup, and OKF components (`tests/unit/`).
- `typesafe-sdk` >= 0.7.2 - System-One CLM evaluation client interfacing with Modal endpoint.
- `google-genai` >= 2.0.0 - Dynamic Objective Knowledge Framework (OKF) macroeconomic updater.

## Key Dependencies

- `typesafe-sdk` (>=0.7.2) - Client library communicating with Contrastive Language Model (CLM-8B) server on Modal for zero-hallucination probability projection `P(Bullish), P(Bearish), P(Neutral)`.
- `google-genai` (>=2.0.0) - Official Google GenAI SDK for updating macroeconomic rules via Gemini flash model fallbacks.
- `psycopg2-binary` (>=2.9.10) - PostgreSQL database driver managing Supabase connection pooling and data transactions.
- `pandas` (>=2.2.3) - Time-series manipulation, exponential moving averages (EMA), and tabular analysis.
- `feedparser` (>=6.0.0) - Multi-format RSS parsing across regional Google News and financial publishers.
- `alpaca-py` (>=0.40.0) - Order routing and execution integration for paper trading.
- `streamlit` - Institutional quantitative web terminal.
- `plotly` - Unified multi-index sentiment visualization.
- `requests` (>=2.31.0) - Synchronous HTTP dispatch and API health probing.

## Configuration

- Managed via OS environment variables and `.env`:
- `.streamlit/config.toml` - Streamlit server and theme configurations.
- `src/config/market_registry.json` - Declarative configuration of regional markets, indices, tickers, and locales.
- `src/config/asset_classes.json` - Asset class criteria definitions.

## Platform Requirements

- Cross-platform: Windows, macOS, Linux supported.
- Devcontainer definition: `.devcontainer/devcontainer.json`.
- Database: Managed PostgreSQL (Supabase) with `uuid-ossp` extension and BRIN indexes.
- Dashboard: Streamlit Cloud / Docker container.
- AI Worker: Modal serverless GPU endpoint running CLM-8B.
- Ingestion & Cron: GitHub Actions scheduled workflows (`.github/workflows/ci.yml`, `update_okf.yml`).

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Code Style & Formatting

- **Standard:** PEP 8 Python style conventions.
- **Typing:** Extensive use of Python standard library `typing` (`Optional`, `Dict`, `List`, `Tuple`, `Any`, `Set`) across core business logic (e.g. `src/ingestion/classifier.py`, `src/ingestion/dedup.py`).
- **Imports:** Structured in logical groupings:

## Design Patterns & Idioms

- System configuration (regions, indices, tickers, economic anchors, currency, locales) is stored declaratively in `src/config/market_registry.json`.
- Python helper functions (`load_market_registry()`, `get_region_meta()`, `build_rss_feeds()`) expose clean, immutable accessors to decouple market definitions from business logic.
- Pattern matching for index tickers, constituent names, and economic anchors are pre-compiled into regexes with word boundaries (`\b(?:...)\b`) during `__init__()`.
- Sorted by token length descending to ensure specific multi-word tokens match before shorter substrings.
- Singleton accessor `get_db_client()` manages a thread-safe `psycopg2.pool.ThreadedConnectionPool`.
- Context manager `get_connection()` checks `_is_alive(conn)` via lightweight `SELECT 1` queries before granting connections.
- Broken or disconnected sockets are evicted via `pool.putconn(conn, close=True)` to prevent pool poisoning.
- Heavy UI containers that receive user interactions (e.g., filter dropdowns, news stream sentiment pills) are wrapped in `@st.fragment` functions.
- Prevents expensive top-to-bottom script re-execution, database reloading, and style re-computation on user widget changes.
- Dynamic account-level model capability inspection (`client.models.list()`) combined with structured priority lists.
- Strict pacing via rate-guards (`MIN_REQUEST_INTERVAL = 6.0s`) to stay deterministically under free-tier API quotas.

## Error Handling & Logging

- Built-in `logging` module configured with timestamps and level: `logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")`.
- Structured tags inside log statements for rapid debugging:
- External API calls and LLM outputs are defensive against payload variations:

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## Pattern Overview

- **Decoupled Pipeline Architecture:** Ingestion, Sentiment Classification, OKF Knowledge Updating, Signal Generation, and UI Presentation operate as independently runnable modules.
- **Vertical Partitioning in Database:** Clean separation between the fast time-series analytical layer (`event_signals`) and the heavy textual payload layer (`event_payloads`).
- **Deterministic AI Scoring:** Replacement of non-deterministic generative LLMs with Contrastive Language Models projecting onto normalized choice probabilities `P(Bullish), P(Bearish), P(Neutral)` with continuous spread calculation.
- **Reactive Streamlit Dashboard with Partial Fragments:** UI updates utilize isolated `@st.fragment` containers to update news streams and time-series plots without full-page script re-runs.

## Layers

- **Purpose:** Discovers, fetches, normalizes, deduplicates, and filters global financial news.
- **Components:**
- **Depends on:** `src/config/market_registry.py`.
- **Used by:** `src/main.py` pipeline orchestrator.
- **Purpose:** Maintains real-time institutional macroeconomic policy rules (Objective Knowledge Framework) per region.
- **Components:**
- **Depends on:** Google GenAI SDK, `src/config/market_registry.py`.
- **Used by:** AI inference layer as prompt conditioning context.
- **Purpose:** Evaluates financial event text conditioned by regional OKF rules and converts it into calibrated directional sentiment scores in `[-1.0, 1.0]`.
- **Components:**
- **Depends on:** `typesafe_sdk`, `knowledge/*.okf.md`.
- **Used by:** Ingestion pipeline before database insertion.
- **Purpose:** Manages PostgreSQL connections and provides resilient pooling.
- **Components:**
- **Depends on:** `psycopg2`.
- **Used by:** Ingestion pipeline, cleanup scripts, and Streamlit dashboard.
- **Purpose:** Computes exponential moving averages across regional sentiment scores and executes paper trades.
- **Components:**
- **Depends on:** `alpaca-py`, `pandas`.
- **Used by:** Scheduled cron tasks.
- **Purpose:** Institutional terminal providing interactive multi-index optimism tracking and live news streaming.
- **Components:**
- **Depends on:** `streamlit`, `plotly`, `pandas`, `src/database/client.py`.

## Data Flow

## Key Abstractions

- `RegionalAffinityClassifier` (`src/ingestion/classifier.py`): Pattern matching engine with pre-compiled regex trees for index tickers (3.0 weight), constituents (2.0 weight), and economic anchors (1.0 weight).
- `NewsDeduplicator` (`src/ingestion/dedup.py`): Fingerprint hashing engine extracting core alpha-numeric text for cross-feed deduplication.
- `SupabasePoolClient` (`src/database/client.py`): Threaded connection pool manager with pre-checkout `_is_alive()` validation and context-managed broken connection eviction.
- `render_dashboard_body()` (`src/ui/app.py`): `@st.fragment`-isolated render tree preventing full-page reloads on filter changes.

## Entry Points

- **`src/main.py`:** Core pipeline entry point. Executed via CLI or GitHub Actions to run ingestion, AI scoring, and signal execution.
- **`src/ui/app.py`:** Frontend entry point. Executed via `streamlit run src/ui/app.py`.
- **`src/knowledge_engine/okf_updater.py`:** Standalone knowledge engine worker executed on schedule via `.github/workflows/update_okf.yml`.
- **`scripts/db_cleanup.py` & `scripts/reclassify_database.py`:** Database maintenance utilities.

## Error Handling & Resilience

- **Database Connection Dropout:** Remote Supabase poolers disconnect idle clients. `SupabasePoolClient` catches `OperationalError` / `InterfaceError`, marks connection broken with `close=True`, and resets the pool if all connections are stale.
- **AI Model Rate Limiting & 503 Outages:** `okf_updater.py` dynamically queries account model lists, loops through a tiered fallback priority, and enforces mandatory minimum sleep intervals (`MIN_REQUEST_INTERVAL = 6.0s`).
- **Formatting Hallucinations:** `src/main.py` guards against unexpected LLM output structures, ensuring robust parsing with safe fallbacks to neutral score.

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| gsp-doc-sync | >- Synchronizes and updates the Global Sentiment Platform (GSP) documentation suite (README.md, docs/sentiment_math.md, docs/architecture_and_workflow.md, and mvp_workflow.md artifact) whenever new features, AI inference logic, scoring math, ingestion feeds, database schemas, or UI components are modified. | `.agents/skills/gsp-doc-sync/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
