---
last_mapped_commit: cf96f4d0048d4bf12ec1ec9d2a683bd1077373a2
last_mapped_at: 2026-10-05
---
# Architecture

**Analysis Date:** 2026-10-05

## Pattern Overview

**Overall:** Event-Driven Quantitative Macro-Sentiment Intelligence & Signal Engine

**Key Characteristics:**
- **Decoupled Pipeline Architecture:** Ingestion, Sentiment Classification, OKF Knowledge Updating, Signal Generation, and UI Presentation operate as independently runnable modules.
- **Vertical Partitioning in Database:** Clean separation between the fast time-series analytical layer (`event_signals`) and the heavy textual payload layer (`event_payloads`).
- **Deterministic AI Scoring:** Replacement of non-deterministic generative LLMs with Contrastive Language Models projecting onto normalized choice probabilities `P(Bullish), P(Bearish), P(Neutral)` with continuous spread calculation.
- **Reactive Streamlit Dashboard with Partial Fragments:** UI updates utilize isolated `@st.fragment` containers to update news streams and time-series plots without full-page script re-runs.

## Layers

**1. Ingestion Layer (`src/ingestion/`):**
- **Purpose:** Discovers, fetches, normalizes, deduplicates, and filters global financial news.
- **Components:**
  - `poller.py`: Asynchronous feed poller fetching multi-region RSS sources concurrently using `aiohttp`.
  - `dedup.py`: `NewsDeduplicator` utilizing regex-normalized `canonical_fingerprint()` to drop intra-batch and cross-run duplicates.
  - `classifier.py`: `RegionalAffinityClassifier` evaluating news content against index tickers, constituent corporations, and macroeconomic anchors with regex boundary scoring to reject cross-region contaminants.
- **Depends on:** `src/config/market_registry.py`.
- **Used by:** `src/main.py` pipeline orchestrator.

**2. Knowledge Engine Layer (`src/knowledge_engine/`, `knowledge/`):**
- **Purpose:** Maintains real-time institutional macroeconomic policy rules (Objective Knowledge Framework) per region.
- **Components:**
  - `okf_updater.py`: Automated generator querying Google GenAI with regional geotargeted news and dynamic model fallbacks to keep rule files up to date.
  - `knowledge/*.okf.md`: Human- and machine-readable macroeconomic condition-action rule contracts for IN, US, UK, JP.
  - `knowledge/*.okf.json`: Benchmark constituent lists for supported indices (Nifty 50, S&P 500, FTSE 100, Nikkei 225, etc.).
- **Depends on:** Google GenAI SDK, `src/config/market_registry.py`.
- **Used by:** AI inference layer as prompt conditioning context.

**3. AI Engine / Inference Layer (`src/ai_engine/`, `src/main.py`):**
- **Purpose:** Evaluates financial event text conditioned by regional OKF rules and converts it into calibrated directional sentiment scores in `[-1.0, 1.0]`.
- **Components:**
  - `main.py::score_sentiment()`: Formats prompt with bipolar criteria (Bullish vs Bearish) and queries TypeSafe CLM-8B client.
  - `inference.py` / `modal_app.py`: Serverless deployment wrapper on Modal.
- **Depends on:** `typesafe_sdk`, `knowledge/*.okf.md`.
- **Used by:** Ingestion pipeline before database insertion.

**4. Data Access Layer (`src/database/`):**
- **Purpose:** Manages PostgreSQL connections and provides resilient pooling.
- **Components:**
  - `client.py`: `SupabasePoolClient` singleton with thread-safe pooling, TCP keepalive probes, and dead connection auto-recycling.
  - `schemas.sql`: Schema DDL definitions with B-tree and BRIN indexes.
- **Depends on:** `psycopg2`.
- **Used by:** Ingestion pipeline, cleanup scripts, and Streamlit dashboard.

**5. Signal & Execution Layer (`src/signal_engine/`):**
- **Purpose:** Computes exponential moving averages across regional sentiment scores and executes paper trades.
- **Components:**
  - `ema.py`: Mathematical EMA calculator across time series.
  - `cron_jobs.py`: Crossover evaluation logic and Alpaca order dispatch.
- **Depends on:** `alpaca-py`, `pandas`.
- **Used by:** Scheduled cron tasks.

**6. Presentation Layer (`src/ui/`):**
- **Purpose:** Institutional terminal providing interactive multi-index optimism tracking and live news streaming.
- **Components:**
  - `app.py`: Streamlit application with custom CSS styling, dynamic Light/Dark mode switching, Plotly visualization, and isolated fragment rendering.
- **Depends on:** `streamlit`, `plotly`, `pandas`, `src/database/client.py`.

## Data Flow

**Typical Ingestion & Inference Lifecycle:**
1. **Trigger:** GitHub Actions cron schedule triggers `python src/main.py`.
2. **Fetch:** `FeedPoller` issues asynchronous requests to all configured RSS feeds for IN, US, UK, and JP.
3. **Filter & Dedup:**
   - Headlines are cleaned of HTML tags and publisher suffixes.
   - `canonical_fingerprint()` checks against recent database records (last 48 hours).
   - `RegionalAffinityClassifier` checks regional affinity against index tickers and constituent corporations, rejecting contaminants.
4. **Scoring:** Fresh headlines are conditioned on the appropriate regional OKF markdown rules and submitted to the TypeSafe CLM model.
5. **Score Derivation:** Continuous directional score is computed from choice probabilities:
   $$S_{rel} = \frac{P(\text{Bullish}) - P(\text{Bearish})}{P(\text{Bullish}) + P(\text{Bearish}) + \epsilon}$$
   $$M = |S_{rel}| \times (1.0 - 0.5 \times P(\text{Neutral}))$$
   $$\text{Score} = \text{sign}(S_{rel}) \times M$$
6. **Persistence:** `event_signals` records the scalar score; `event_payloads` records the headline and applied OKF rules under a shared UUID.
7. **Signal Calculation:** `signal_engine` computes 4-period EMA to detect regime crossovers and optionally routes orders to Alpaca.
8. **Visualization:** UI loads records from `event_signals` via connection pooler and renders real-time multi-index surfaces.

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

---

*Architecture analysis: 2026-10-05*
*Update when major patterns change*
