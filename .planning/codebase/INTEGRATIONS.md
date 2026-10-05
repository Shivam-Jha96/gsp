---
last_mapped_commit: cf96f4d0048d4bf12ec1ec9d2a683bd1077373a2
last_mapped_at: 2026-10-05
---
# External Integrations

**Analysis Date:** 2026-10-05

## External APIs & Services

**1. TypeSafe AI / Modal Serverless CLM-8B**
- **Purpose:** Deterministic financial sentiment evaluation using Contrastive Language Modeling (CLM).
- **Service Endpoint:** `https://shivam-jha96--clm-macro-engine-clm-server.modal.run`
- **Client:** `typesafe_sdk.TypeSafeClient` (`src/main.py`, `src/ai_engine/inference.py`).
- **Auth:** `TYPESAFE_API_KEY` environment variable.
- **Payload:** Dispatches targeted financial news event text conditioned on OKF regional macro rules and asset-class criteria.
- **Response:** Raw choice probabilities `P(Bullish)`, `P(Bearish)`, `P(Neutral)`.

**2. Google GenAI (Gemini Models)**
- **Purpose:** Automated analysis and generation of institutional Objective Knowledge Framework (OKF) macroeconomic trading rules.
- **SDK:** `google.genai.Client` (`src/knowledge_engine/okf_updater.py`).
- **Auth:** `GEMINI_API_KEY` environment variable.
- **Models:** Dynamic model discovery with resilient fallback pool (`gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`).
- **Rate Guard:** Enforced `MIN_REQUEST_INTERVAL = 6.0s` and `INTER_REGION_DELAY = 10.0s` to operate safely within Google free-tier rate limits (15 RPM).

**3. Alpaca Paper Trading API**
- **Purpose:** Automated directional order execution triggered by EMA crossover signals.
- **Client:** `alpaca.trading.client.TradingClient` (`src/signal_engine/cron_jobs.py`).
- **Auth:** `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`.
- **Order Model:** Market orders submitted via `MarketOrderRequest` with GTC (`TimeInForce.GTC`) for equities (default: `SPY`).

**4. Google News RSS Feeds**
- **Purpose:** Continuous real-time financial news ingestion across global regions.
- **Protocol:** HTTP GET over RSS using `aiohttp` and `feedparser`.
- **Geotargeting:** Built dynamically per region (`gl`, `hl`, `ceid`) from `src/config/market_registry.json`.
- **Queries:** General index queries and institutional publisher-scoped queries (e.g. Reuters).

## Databases & Storage

**PostgreSQL (Supabase)**
- **Connection Mode:** Session / Transaction pooler (typically port 6543 or 5432).
- **Pool Management:** `psycopg2.pool.ThreadedConnectionPool` wrapped by `SupabasePoolClient` (`src/database/client.py`).
- **Connection Health:** Proactive TCP keepalives (`keepalives=1`, `keepalives_idle=30`, `keepalives_interval=10`, `keepalives_count=5`), pre-checkout liveness validation (`SELECT 1`), and dead connection recycling.
- **Tables:**
  - `event_signals`: Mathematical layer storing `id` (UUID), `index_ticker`, `market_region`, `timestamp`, `sentiment_score`.
  - `event_payloads`: Document layer storing `id` (1-to-1 foreign key with `ON DELETE CASCADE`), `raw_text`, `applied_okf_rules`, and `metadata` (JSONB).

## Webhooks & Automation Triggers

**GitHub Actions Workflows (`.github/workflows/`)**
- `ci.yml`: Scheduled cron execution of the ingestion and signal engine pipeline every 2 hours (`0 */2 * * *`) and on push/workflow_dispatch.
- `update_okf.yml`: Automated weekly / scheduled macroeconomic OKF rule updates via Google Gemini AI (`src/knowledge_engine/okf_updater.py`).
- `db_cleanup.yml`: Scheduled maintenance workflow running `scripts/db_cleanup.py` to prune historical noise and optimize storage.
- `reclassify_db.yml`: Database batch reclassification utility (`scripts/reclassify_database.py`) to fix regional misclassifications.
- `deploy.yml`: Deployment triggers for remote infrastructure.

---

*Integrations analysis: 2026-10-05*
*Update after service or integration changes*
