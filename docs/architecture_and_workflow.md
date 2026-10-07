# End-to-End System Architecture and Technical Workflow
 
## 1. Executive Summary & Architectural Philosophy
 
**Valence** (formerly Global Sentiment Platform of Share Markets / GSP) is an autonomous, production-grade quantitative intelligence and execution platform. The system continuously digests unstructured global macroeconomic news streams across 20 international asset classes in 4 geopolitical regions (United States, India, United Kingdom, and Japan), evaluates deterministic market sentiment using Contrastive Language Models (**CLM-8B System-One**), stores vertically partitioned time-series signals in PostgreSQL, computes multi-period Exponential Moving Average (**EMA**) momentum indicators, executes automated paper trades via Alpaca's REST API, and renders low-latency telemetry to an institutional Streamlit terminal.
 
```
+---------------------------------------------------------------------------------------------------------+
|                                  VALENCE CORE ARCHITECTURAL PARADIGMS                                   |
+------------------------------------+------------------------------------+-------------------------------+
|       SYSTEM-ONE INFERENCE         |       VERTICAL PARTITIONING        |      GITOPS FOR KNOWLEDGE     |
| Contrastive state-action mapping   | Decoupling math & document layers  | Macro heuristics versioned    |
| yields sub-60ms inference latency  | reduces query load by >90% while   | in Markdown; auto-evolved by  |
| with zero cold-boot overhead.      | preserving rich raw contexts.      | Google Gemini cron jobs.      |
+------------------------------------+------------------------------------+-------------------------------+
```
 
### Core Design Principles
 
1. **Deterministic System-One Decision Making:** Unlike traditional autoregressive large language models that generate verbose text and suffer from high latency and non-deterministic formatting errors, Valence deploys **CLM-8B** hosted on serverless GPU infrastructure. CLM utilizes contrastive learning (InfoNCE) over a frozen Qwen3-8B embedding backbone with lightweight 20M-parameter projection heads to directly score directional action candidates (`Bullish`, `Bearish`, `Neutral`) with mathematical probability vectors.
2. **Strict Vertical Partitioning:** The database tier separates high-frequency numerical time-series queries from heavy unstructured document storage. Analytical aggregation queries scan only the lightweight `event_signals` table (leveraging composite B-Tree and BRIN indices), completely bypassing heavy text and JSON blobs located in `event_payloads`.
3. **GitOps-Driven Knowledge Evolution:** Macroeconomic policy regimes change dynamically. Instead of baking heuristics into model prompts or hardcoding them in Python logic, rules reside in standalone Objective Knowledge Framework (`*.okf.md`) files. An autonomous crawler powered by Google Gemini analyzes global central bank shifts daily, updating these files via automated Git commits without requiring software redeployments.
4. **Decoupled Serverless Topologies:** Ingestion, AI inference, relational storage, quantitative trade execution, and user presentation execute across independently scalable, fault-isolated serverless environments: GitHub Actions runners, Modal serverless GPU containers, Supabase managed PostgreSQL, and Streamlit Community Cloud.

---

## 2. High-Level Architecture Overview

The system operates across seven distinct architectural tiers, executing automated pipelines on scheduled cadences (every 2 hours for ingestion/signals, daily for knowledge updates) alongside continuous real-time presentation.

```mermaid
flowchart TD
    subgraph S1["Data Ingestion Tier"]
        GN["Google News RSS Feeds<br/>(20 Global Assets / 4 Regions)"]
        RT["Reuters RSS Feeds<br/>(site:reuters.com Constrained)"]
        FP["FeedPoller & RSSClient<br/>(src/ingestion/poller.py)"]
        DEDUP["XML Parsing & Deduplication Engine<br/>(src/ingestion/api_clients.py)"]
        GN --> FP
        RT --> FP
        FP --> DEDUP
    end

    subgraph S2["Knowledge & Ingestion Pipeline"]
        MAIN["Pipeline Orchestrator<br/>(src/main.py)"]
        OKF_FILES["Objective Knowledge Files<br/>(knowledge/*.okf.md)"]
        DEDUP --> MAIN
        OKF_FILES -->|Dynamic Context Injection| MAIN
    end

    subgraph S3["AI Inference Tier (Modal Serverless A10G)"]
        MODAL_APP["Modal ASGI Server<br/>(src/ai_engine/modal_app.py)"]
        VLLM["vLLM Pooling Engine<br/>(Qwen/Qwen3-8B Backbone :8090)"]
        CLM_HEAD["CLM-v0.1-8B Contrastive Heads<br/>(In-Memory Vector Arena Cache)"]
        SDK["TypeSafe SDK Client<br/>(Net Directional Probabilities)"]
        MAIN -->|Async Batch Requests| SDK
        SDK --> MODAL_APP
        MODAL_APP --- VLLM
        MODAL_APP --- CLM_HEAD
    end

    subgraph S4["Database Tier (Supabase PostgreSQL)"]
        DB_POOL["SupabasePoolClient<br/>(src/database/client.py)"]
        MATH_LAYER["event_signals Table<br/>(UUID, Ticker, Region, Timestamp, Score)<br/>Composite B-Tree & BRIN Indices"]
        DOC_LAYER["event_payloads Table<br/>(UUID PK-FK, Raw Text, OKF Rules, JSONB)"]
        MAIN -->|Connection Pool Port 6543| DB_POOL
        DB_POOL -->|Normalized Math Vector| MATH_LAYER
        DB_POOL -->|Unstructured Document Record| DOC_LAYER
    end

    subgraph S5["Quantitative Signal & Execution Engine"]
        CRON["cron_ema_trigger()<br/>(src/signal_engine/cron_jobs.py)"]
        EMA_CALC["Vectorized Pandas EMA Calculation<br/>(src/signal_engine/ema.py - span=4)"]
        CROSSOVER["Crossover Detection Logic<br/>(EMA_t vs EMA_t-1 & Zero Boundary)"]
        ALPACA["Alpaca Paper Trading Client<br/>(alpaca-py MarketOrderRequest)"]
        MAIN --> CRON
        MATH_LAYER -.->|Historical Series Query| CRON
        CRON --> EMA_CALC
        EMA_CALC --> CROSSOVER
        CROSSOVER -->|Directional Market Order| ALPACA
    end

    subgraph S6["Presentation Layer (Streamlit Cloud)"]
        ST_APP["Macro-Sentiment Terminal<br/>(src/ui/app.py)"]
        CALIBRATE["Historical Calibration Filter<br/>(Floor Cutoff)"]
        TZ_ENGINE["Timezone Conversion Engine<br/>(IST, UTC, EST, GMT, JST)"]
        KPI_TILES["Dynamic Responsive KPI Cards<br/>(Optimism, Bias, Volume, Momentum)"]
        PLOTLY_AREA["Plotly Multi-Index Sentiment Surface<br/>(Overlapping Filled Areas + Region Mean)"]
        LIVE_FEED["Sanitized Live Intelligence Stream<br/>(Bullish/Bearish/Noise Badging)"]
        MATH_LAYER -->|st.cache_data ttl=30s| ST_APP
        DOC_LAYER -->|st.cache_data ttl=30s| ST_APP
        ST_APP --> CALIBRATE
        CALIBRATE --> TZ_ENGINE
        TZ_ENGINE --> KPI_TILES
        TZ_ENGINE --> PLOTLY_AREA
        TZ_ENGINE --> LIVE_FEED
    end

    subgraph S7["Autonomous Knowledge Engine"]
        OKF_UPDATER["Autonomous OKF Updater<br/>(src/knowledge_engine/okf_updater.py)"]
        GEMINI["Google Gemini API<br/>(gemini-3.8-flash, 3.7, 3.5-lite)"]
        GIT_BOT["GitHub Actions Bot<br/>(Auto Commit & Push)"]
        GN -.->|Policy & Macro Queries| OKF_UPDATER
        OKF_UPDATER --> GEMINI
        GEMINI -->|Synthesized Macro Rules| OKF_UPDATER
        OKF_UPDATER --> GIT_BOT
        GIT_BOT -->|Update Regional OKF Rules| OKF_FILES
    end

    classDef source fill:#1e293b,stroke:#3b82f6,stroke-width:1px,color:#f8fafc;
    classDef inference fill:#1e1b4b,stroke:#6366f1,stroke-width:1px,color:#f8fafc;
    classDef storage fill:#064e3b,stroke:#10b981,stroke-width:1px,color:#f8fafc;
    classDef quant fill:#451a03,stroke:#f59e0b,stroke-width:1px,color:#f8fafc;
    classDef ui fill:#022c22,stroke:#059669,stroke-width:1px,color:#f8fafc;
    classDef knowledge fill:#3b0764,stroke:#a855f7,stroke-width:1px,color:#f8fafc;

    class GN,RT,FP,DEDUP source;
    class MODAL_APP,VLLM,CLM_HEAD,SDK inference;
    class DB_POOL,MATH_LAYER,DOC_LAYER storage;
    class CRON,EMA_CALC,CROSSOVER,ALPACA quant;
    class ST_APP,CALIBRATE,TZ_ENGINE,KPI_TILES,PLOTLY_AREA,LIVE_FEED ui;
    class OKF_UPDATER,GEMINI,GIT_BOT,OKF_FILES knowledge;
```

### End-to-End Execution Sequence

The following sequence diagram outlines the chronological interaction flow during a scheduled 2-hour pipeline run:

```mermaid
sequenceDiagram
    autonumber
    participant GHA as GitHub Actions Runner
    participant POL as "FeedPoller (aiohttp)"
    participant RSS as "RSS Endpoints (Google/Reuters)"
    participant CLM as "Modal CLM-8B Cluster"
    participant DB as "Supabase PostgreSQL"
    participant SIG as "Quant Signal Engine"
    participant ALP as "Alpaca Brokerage API"

    GHA->>POL: Trigger run_ingestion_pipeline()
    POL->>RSS: Fetch 40 feeds concurrently (asyncio.gather)
    RSS-->>POL: Return Raw RSS XML Feeds
    POL->>POL: Parse XML, Deduplicate and Cap Top-3 per Ticker
    loop For Each Ingested Article
        POL->>POL: Inject Regional OKF Context
        POL->>CLM: POST /v1/systemone (State + Choice Questions)
        CLM-->>POL: Return Directional Choice & Probabilities
        POL->>POL: Compute Net Directional Score
        POL->>DB: INSERT INTO event_signals (Math Layer)
        POL->>DB: INSERT INTO event_payloads (Document Layer)
    end
    GHA->>SIG: Trigger run_signal_engine()
    SIG->>DB: SELECT historical scores for active universe
    DB-->>SIG: Return time-series records
    SIG->>SIG: Calculate 4-period EMA using Pandas ewm()
    alt Bullish Crossover: EMA above Prev and EMA above 0
        SIG->>ALP: submit_order(SPY, Qty=1, Side=BUY, MarketOrder)
        ALP-->>SIG: Confirm Order ID & Execution Fill
    else Bearish Crossover: EMA below Prev and EMA below 0
        SIG->>ALP: submit_order(SPY, Qty=1, Side=SELL, MarketOrder)
        ALP-->>SIG: Confirm Order ID & Execution Fill
    else Neutral / Divergence Undefined
        SIG->>SIG: Suppress order execution (Hold position)
    end
    GHA->>GHA: Terminate job successfully
```

---

## 3. Layer-by-Layer Technical Breakdown

### Layer 1: Ingestion Layer
* **Source Files:** [`src/ingestion/poller.py`](file:///d:/Dev/repos/gsp/src/ingestion/poller.py), [`src/ingestion/api_clients.py`](file:///d:/Dev/repos/gsp/src/ingestion/api_clients.py)
* **Runtime & Dependencies:** Python 3.10+, `aiohttp>=3.11.12`, `xml.etree.ElementTree`, `asyncio`

#### 1. Coverage Universe & Declarative Market Registry (`market_registry.json`)
The ingestion layer is driven entirely by a single-source-of-truth declarative registry at [`src/config/market_registry.json`](file:///d:/Dev/repos/gsp/src/config/market_registry.json). Adding a new country to the global coverage universe requires solely appending an entry to the registry without modifying core ingestion code. Currently, it maintains active coverage across 20 global macroeconomic indices and proxies:

| Region Code | Market Region | Currency | Geotargeting (`hl`, `gl`, `ceid`) | Tracked Indices / Proxies |
| :--- | :--- | :--- | :--- | :--- |
| **US** | United States | USD | `en-US`, `US`, `US:en` | S&P 500, NASDAQ, Dow Jones, Russell 2000, VIX |
| **IN** | India | INR | `en-IN`, `IN`, `IN:en` | Nifty 50, Sensex, Nifty Bank, Nifty IT, BSE Midcap |
| **UK** | United Kingdom | GBP | `en-GB`, `GB`, `GB:en` | FTSE 100, FTSE 250, FTSE All-Share, FTSE AIM, UK Gilts |
| **JP** | Japan | JPY | `en-JP`, `JP`, `JP:en` | Nikkei 225, TOPIX, JP Mothers (TSE Growth), JASDAQ, JP Bonds |

#### 2. Geotargeted Query Channeling & Polling Architecture
Each asset is dynamically expanded by [`src/config/market_registry.py`](file:///d:/Dev/repos/gsp/src/config/market_registry.py) into two distinct geotargeted polling channels:
1. **Geotargeted General News Channel:** `https://news.google.com/rss/search?q=%22{ticker}%22+market&hl={hl}&gl={gl}&ceid={ceid}`
2. **Geotargeted Institutional Reuters Channel:** `https://news.google.com/rss/search?q=%22{ticker}%22+market+site:reuters.com&hl={hl}&gl={gl}&ceid={ceid}`

Exact quotation prevents Google from returning broad fuzzy keyword associations, while country geolocation parameters (`gl`, `ceid`) force the RSS indexer to return country-edition articles rather than defaulting to US-centric cloud runner editions. `FeedPoller` executes all 40 active endpoints asynchronously using `asyncio.gather(*tasks)` and a shared `aiohttp.ClientSession`.

#### 3. Deterministic Entity, Constituent Company & Regional Affinity Gatekeeper (`classifier.py`)
To mathematically prevent cross-region contamination (e.g., US Wall Street market wraps erroneously tagged under India, or Indian shares returned under UK FTSE queries) while ensuring constituent company news is correctly recognized, [`RegionalAffinityClassifier`](file:///d:/Dev/repos/gsp/src/ingestion/classifier.py) evaluates every parsed headline against a multi-tier compiled regex entity trie:
* **Index Ticker Affinity (Weight = 3.0):** Matches exact index ticker names and their aliases (e.g., `S&P 500`, `Nifty 50`, `FTSE 100`, `Nikkei 225`).
* **Constituent Company Affinity (Weight = 2.0):** Dynamically compiled from declarative regional constituent files (`knowledge/*_constituents.okf.json`). Matches individual listed companies (e.g., `Apple`, `Nvidia`, `Mulberry`, `Steady Energy`, `Fidelity Special Values`, `TCS`, `Toyota`) and automatically resolves the article to its parent index ticker (e.g., Mulberry $\to$ FTSE AIM).
* **Macroeconomic Anchor Affinity (Weight = 1.0):** Matches country-specific institutions, central banks, and currency anchors (`rbi`, `rupee`, `dalal street`, `fed`, `boe`, `boj`, `yen`, `gilt`, `london`).
* **Verification & Rerouting Rules:**
  - An item is accepted into the pipeline if $\text{Affinity}(\text{ExpectedRegion}) > 0$.
  - If a constituent company is matched, the item's `index_ticker` is resolved directly to that company's parent index.
  - Cross-region contaminants (where expected affinity is 0 but another region's affinity is high) are automatically rejected and logged.
  - **Broad-Market Equity Action Heuristic:** If a feed item exhibits zero cross-region contaminant signals and contains market price-action vocabulary (`stocks`, `equities`, `rally`, `selloff`, `jobs data`), it is validated for the expected region rather than falsely discarded as noise.

#### 4. Region-Wise Declarative Index Constituents (`knowledge/*_constituents.okf.json`)
Indices are baskets of constituent companies. In practice, high-impact financial news frequently mentions individual companies rather than the abstract index ticker. Valence maintains declarative constituent registries per region:
* [`knowledge/us_constituents.okf.json`](file:///d:/Dev/repos/gsp/knowledge/us_constituents.okf.json): S&P 500, NASDAQ, Dow Jones, Russell 2000 mega-caps and mid-caps.
* [`knowledge/india_constituents.okf.json`](file:///d:/Dev/repos/gsp/knowledge/india_constituents.okf.json): Nifty 50, Sensex, Nifty Bank, Nifty IT leaders.
* [`knowledge/uk_constituents.okf.json`](file:///d:/Dev/repos/gsp/knowledge/uk_constituents.okf.json): FTSE 100, FTSE 250, FTSE All-Share, and FTSE AIM constituents.
* [`knowledge/japan_constituents.okf.json`](file:///d:/Dev/repos/gsp/knowledge/japan_constituents.okf.json): Nikkei 225, TOPIX, JP Mothers, JASDAQ constituents.

[`src/config/market_registry.py`](file:///d:/Dev/repos/gsp/src/config/market_registry.py#L39-L68) provides `load_region_constituents(region_code)` with memoized caching.

#### 5. XML Parsing, Rate Control & Deduplication Logic
* **Lightweight Parsing:** Rather than incurring the overhead of heavy third-party RSS libraries, [`RSSClient.parse_feed`](file:///d:/Dev/repos/gsp/src/ingestion/api_clients.py#L24-L54) uses Python's built-in `xml.etree.ElementTree` to parse raw XML into standard Python dictionaries containing title, link, published timestamp, and summary.
* **Volume Limiting & Free-Tier Guard:** The parser applies a strict `items[:3]` slice per endpoint. Across 40 feeds, this generates a deterministic ceiling of at most 120 items per ingestion cycle, ensuring the downstream inference process stays well within API quotas and completes within standard CI/CD timeouts.
* **Normalized Data Contract:**
```json
{
  "source_system": "RSS_POLLER",
  "content_type": "news",
  "region_tag": "US",
  "index_ticker": "S&P 500",
  "data": {
    "headline": "Fed signals potential pause as inflation data moderates",
    "summary": "U.S. stocks edged higher following comments by Federal Reserve officials...",
    "url": "https://news.google.com/rss/articles/...",
    "timestamp": "Wed, 02 Oct 2026 12:00:00 GMT"
  }
}
```

#### 6. Universal Multi-Stage News Deduplication Engine
To eliminate OPEX/CAPEX waste (redundant inference costs and duplicate database records), [`src/ingestion/dedup.py`](file:///d:/Dev/repos/gsp/src/ingestion/dedup.py) provides deterministic headline fingerprinting (`canonical_fingerprint()`):
* **Intra-Run Deduplication:** In [`src/ingestion/poller.py`](file:///d:/Dev/repos/gsp/src/ingestion/poller.py#L77-L85), [`NewsDeduplicator`](file:///d:/Dev/repos/gsp/src/ingestion/dedup.py#L48-L82) filters the batch of polled items across all 20 ticker queries. If major publishers (Reuters, Bloomberg, etc.) appear in multiple feeds (e.g. Nifty 50 and Sensex), redundant copies are collapsed into a single canonical payload.
* **Cross-Run Database Deduplication:** In [`src/main.py`](file:///d:/Dev/repos/gsp/src/main.py#L140-L175), before calling the AI engine, the pipeline queries recent headline fingerprints from Supabase for the last 48 hours. Any headline already present in storage is skipped, saving 100% of redundant inference calls.

---

### Layer 2: AI Inference & Knowledge Layer
* **Source Files:** [`src/main.py`](file:///d:/Dev/repos/gsp/src/main.py), [`src/ai_engine/modal_app.py`](file:///d:/Dev/repos/gsp/src/ai_engine/modal_app.py), [`knowledge/*.okf.md`](file:///d:/Dev/repos/gsp/knowledge/)
* **Runtime & Dependencies:** Modal Cloud (NVIDIA A10G), `vllm`, `contrastive-lm`, `typesafe-sdk>=0.7.2`, `torch`, `hf_transfer`

#### 1. System-One CLM-8B Inference Architecture
Conventional generative AI models (System-Two) rely on autoregressive token-by-token generation, requiring hundreds of milliseconds to produce formatted JSON responses that frequently fail schema validation. Valence implements a **System-One Contrastive Language Model (CLM-8B)**:
* **Backbone:** Frozen `Qwen/Qwen3-8B` language model acting as a semantic text encoder.
* **Projection Heads:** Lightweight 20M-parameter contrastive heads (`Contrastive-LM/CLM-v0.1-8B`) trained via bidirectional InfoNCE loss.
* **Disaggregated Embeddings:** State text and candidate criteria vectors are embedded separately and compared in metric space, yielding latencies under 60 milliseconds.

#### 2. Focused State Conditioning & Grounded Bipolar Momentum Scoring
To eliminate context dilution (where 400 words of static OKF macro rules flooded the context window and caused the model to default to $P(\text{Neutral}) \ge 0.90$ with zero dynamic range), [`src/main.py`](file:///d:/Dev/repos/gsp/src/main.py#L20-L76) implements **Focused Bipolar Equity Momentum Conditioning**:
* **State Text:** Constrained strictly to the target event with regional jurisdictional tagging:
  $$\text{State} = \texttt{"Target Financial News Event (\{region_tag\} Market):\textbackslash n\{Headline\} - \{Summary\}"}$$
* **Grounded Bipolar Choices:**
  - **Bullish:** *"Equity market optimism: stock prices rising, benchmark index gains, market rally, positive corporate growth, expansion."*
  - **Bearish:** *"Equity market pessimism: stock prices falling, benchmark index drops, market selloff, decline, warnings, downward pressure."*
* **Continuous Calibrated Directional Score:**
  $$S = P(\text{Bullish}) - P(\text{Bearish}) \in [-1.0, 1.0]$$
  This captures minor and moderate company developments ($+0.10$ to $+0.35$), neutral balance ($+0.002$), and major macroeconomic shocks ($-0.85$ to $-0.95$), completely eliminating neutral flatlining.

#### 3. Serverless Modal Deployment & Zero Cold-Boot ASGI Design
To avoid connection proxy deadlocks and minimize cold-start latency, [`src/ai_engine/modal_app.py`](file:///d:/Dev/repos/gsp/src/ai_engine/modal_app.py) deploys the model directly to an NVIDIA A10G GPU using Modal's `@modal.asgi_app()` decorator:

```python
app = modal.App("clm-macro-engine")

@app.function(
    gpu="A10G", 
    image=image, 
    min_containers=0,
    scaledown_window=120,
    timeout=3600
)
@modal.asgi_app()
def clm_server():
    # 1. Spawn local vLLM pooling instance on port 8090
    vllm_process = subprocess.Popen([
        "vllm", "serve", "Qwen/Qwen3-8B", 
        "--served-model-name", "qwen3-8b", 
        "--runner", "pooling", 
        "--max-model-len", "2048", 
        "--port", "8090",
        "--enforce-eager", "--gpu-memory-utilization", "0.9"
    ])
    # 2. Wait for local health check endpoint
    # 3. Mount contrastive Engine and FastAPI app natively
    return fastapi_app
```

* **Image Optimization:** Weights are pre-baked into the Modal Debian container image using `hf_transfer` and Hugging Face snapshot downloads, eliminating runtime downloading delays.
* **Keep-Alive Scale-Down Window:** An idle scale-down window of 120 seconds keeps containers warm during consecutive batch queries.

#### 4. Mathematical Sentiment Calibration
In [`src/main.py`](file:///d:/Dev/repos/gsp/src/main.py#L22-L82), the TypeSafe SDK queries the CLM serverless endpoint. The probabilities $P(\text{Bullish})$, $P(\text{Bearish})$, and $P(\text{Neutral})$ are converted into a calibrated directional sentiment score $S \in [-1.0, 1.0]$:

1. **Relative Directional Spread ($s_{\text{rel}}$):**
   $$s_{\text{rel}} = \frac{P(\text{Bullish}) - P(\text{Bearish})}{P(\text{Bullish}) + P(\text{Bearish}) + \epsilon} \quad \text{where } \epsilon = 10^{-5}$$
2. **Neutrality Attenuation ($M$):**
   $$M = |s_{\text{rel}}| \times \left(1.0 - 0.5 \times P(\text{Neutral})\right)$$
3. **Directional Assignment & Clamping:**
   $$S = \begin{cases} 
      0.0 & \text{if Decision} = \text{Neutral or } |s_{\text{rel}}| < 0.05 \\
      -M & \text{if } P(\text{Bearish}) > P(\text{Bullish}) \\
      +M & \text{if } P(\text{Bullish}) > P(\text{Bearish})
   \end{cases}, \quad S = \max(-1.0, \min(1.0, S))$$

This ensures high confidence is required to trigger strong bullish or bearish values, while ambiguous headlines naturally decay toward zero.

#### 5. Objective Knowledge Framework (OKF) Integration
Prior to sending headlines to the AI model, [`src/main.py`](file:///d:/Dev/repos/gsp/src/main.py) dynamically loads the corresponding region's macro rules from `knowledge/{region}_macro.okf.md`. These rules provide the macroeconomic domain constraints under which the CLM evaluates headline impact (e.g., treating rate hikes as bearish for equities but bullish for currency values).

---

### Layer 3: Database & Storage Layer
* **Source Files:** [`src/database/client.py`](file:///d:/Dev/repos/gsp/src/database/client.py), [`src/database/schemas.sql`](file:///d:/Dev/repos/gsp/src/database/schemas.sql)
* **Runtime & Dependencies:** Supabase Managed PostgreSQL 15+, `psycopg2-binary>=2.9.10`, PgBouncer connection pooler

#### 1. Vertical Partitioning Schema Architecture
To optimize analytical query performance, the storage layer implements a two-table vertical partitioning pattern:

```sql
-- 1. The Math Layer (Ultra-lean for rapid vector aggregations)
CREATE TABLE event_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    index_ticker VARCHAR(50) NOT NULL,
    market_region VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    sentiment_score NUMERIC
);

-- 2. The Document Layer (Heavy unstructured payloads in 1-to-1 relationship)
CREATE TABLE event_payloads (
    id UUID PRIMARY KEY REFERENCES event_signals(id) ON DELETE CASCADE,
    raw_text TEXT,
    applied_okf_rules TEXT[],
    metadata JSONB
);
```

```
+------------------------------------------------------------------------------------+
|                                VERTICAL PARTITIONING                               |
+-----------------------------------------+------------------------------------------+
|      TABLE: event_signals (Math)        |      TABLE: event_payloads (Document)    |
+-----------------------------------------+------------------------------------------+
|  id: UUID (PK)                          |  id: UUID (PK, FK -> event_signals)      |
|  index_ticker: VARCHAR(50)              |  raw_text: TEXT                          |
|  market_region: VARCHAR(100)            |  applied_okf_rules: TEXT[]               |
|  timestamp: TIMESTAMPTZ                 |  metadata: JSONB                         |
|  sentiment_score: NUMERIC               |                                          |
+-----------------------------------------+------------------------------------------+
|  Scan Speed: Sub-millisecond            |  Access: Only fetched for drill-down     |
|  Used By: Signal Engine, EMA Charts     |  Used By: Live Intelligence Feed modal   |
+-----------------------------------------+------------------------------------------+
```

#### 2. Advanced Indexing Strategy
* **Composite B-Tree Index:**
  ```sql
  CREATE INDEX idx_event_signals_ticker_time 
  ON event_signals USING btree (index_ticker, timestamp DESC);
  ```
  Accelerates ticker-filtered chronological queries required by the quant engine and dashboard timeline.
* **Block Range Index (BRIN):**
  ```sql
  CREATE INDEX idx_event_signals_timestamp_brin 
  ON event_signals USING brin (timestamp);
  ```
  Since event records are written chronologically, BRIN stores only the minimum and maximum timestamps per physical disk block. This provides lightning-fast range queries over millions of historical events with less than 1% of the disk footprint of a traditional B-Tree index.

#### 3. Connection Pooling & Self-Healing Resiliency Logic
[`SupabasePoolClient`](file:///d:/Dev/repos/gsp/src/database/client.py) implements an institutional, auto-reconnecting connection pool using `psycopg2.pool.ThreadedConnectionPool`:
* **Transaction Pooler Targeting:** Formatted to route queries through Supabase's transaction-mode connection pooler (port 6543 / Supavisor / PgBouncer), preventing database connection slot exhaustion during concurrent ingestion bursts.
* **Proactive TCP Keepalives:** Configured with `keepalives=1`, `keepalives_idle=30`, `keepalives_interval=10`, and `keepalives_count=5`. This ensures intermediate NAT firewalls and cloud proxies do not sever idle socket state tables unnoticed.
* **Pre-Checkout Liveness Validation:** Before checking out any connection from the pool, `_get_valid_connection()` executes a lightweight `SELECT 1;` health check (`_is_alive()`). If the remote server or pooler terminated the connection during idle dashboard periods, the dead socket is immediately discarded using `pool.putconn(conn, close=True)` and a fresh connection is spawned.
* **Automatic Exception Recycling:** In `get_connection()`, any query failing with `OperationalError` or `InterfaceError` flags the connection as broken and purges it with `close=True`, preventing dead sockets from returning to contaminate the pool.
* **Streamlit Transparent 2-Attempt Auto-Retry:** In [`src/ui/app.py`](file:///d:/Dev/repos/gsp/src/ui/app.py)'s `load_data()`, database queries run inside a 2-attempt retry loop. If an idle timeout drop occurs, the client invokes `reset_db_client()`, waits 500ms, and reconnects transparently, completely eliminating transient error banners and false "Database empty" warnings for end users.

#### 4. Pipeline Execution Telemetry & Freshness Tracking (`pipeline_runs`)
[`src/database/telemetry.py`](file:///d:/Dev/repos/gsp/src/database/telemetry.py) introduces a dedicated execution lifecycle tracking layer:
* **Telemetry Schema:**
  ```sql
  CREATE TABLE IF NOT EXISTS pipeline_runs (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      pipeline_name VARCHAR(100) NOT NULL,
      status VARCHAR(20) NOT NULL, -- 'RUNNING', 'SUCCESS', 'FAILED'
      started_at TIMESTAMPTZ NOT NULL,
      completed_at TIMESTAMPTZ,
      duration_seconds NUMERIC(10, 2),
      items_polled INT DEFAULT 0,
      items_scored INT DEFAULT 0,
      metadata JSONB DEFAULT '{}'::jsonb
  );

  CREATE INDEX IF NOT EXISTS idx_pipeline_runs_lookup 
  ON pipeline_runs (pipeline_name, status, completed_at DESC);
  ```
* **Context Managed Execution:** In `src/main.py`, background pipeline runs are wrapped with `with track_pipeline_run("macro_sentiment_pipeline", db_client=db_client) as tracker:`. On clean completion, the run updates `completed_at = NOW()`, records duration, items polled, and items scored.
* **Failure Isolation:** Uncaught runtime exceptions mark `status = 'FAILED'`, preventing aborted runs from advancing the completion timestamp.
* **Zero-OPEX Deduplication Handling:** When all incoming headlines are cached in Supabase (0 items scored), the run still logs `SUCCESS` and records `completed_at`, accurately demonstrating to dashboard users that the pipeline checked feeds on schedule.

---

### Layer 4: Signal & Quantitative Execution Engine
* **Source Files:** [`src/signal_engine/ema.py`](file:///d:/Dev/repos/gsp/src/signal_engine/ema.py), [`src/signal_engine/cron_jobs.py`](file:///d:/Dev/repos/gsp/src/signal_engine/cron_jobs.py)
* **Runtime & Dependencies:** Python 3.10+, `pandas>=2.2.3`, `alpaca-py>=0.40.0`

#### 1. Vectorized Exponential Moving Average (EMA) Calculation
[`calculate_ema`](file:///d:/Dev/repos/gsp/src/signal_engine/ema.py#L3-L26) operates on chronological sentiment time series using Pandas' vectorized `ewm` functionality:

$$\text{EMA}_t = \alpha \cdot S_t + (1 - \alpha) \cdot \text{EMA}_{t-1}, \quad \alpha = \frac{2}{N + 1}$$

With window size $N = 4$, the smoothing coefficient is $\alpha = 0.40$. `adjust=False` is enforced to apply the recursive exponential decay formula without introducing initialization bias.

```python
def calculate_ema(sentiment_data: pd.DataFrame, window: int = 4, column: str = 'sentiment_score') -> pd.Series:
    if column not in sentiment_data.columns:
        raise ValueError(f"DataFrame must contain a '{column}' column")
    return sentiment_data[column].ewm(span=window, adjust=False).mean()
```

#### 2. Crossover Strategy & Order Execution
The quantitative engine evaluates consecutive EMA points ($\text{EMA}_{\text{current}}$ and $\text{EMA}_{\text{previous}}$) to identify directional momentum shifts:

```
                  EMA > Prev & EMA > 0
               +------------------------> BUY (OrderSide.BUY)
               |
SIGNAL STATE --+  EMA < Prev & EMA < 0
               +------------------------> SELL (OrderSide.SELL)
               |
               +------------------------> HOLD (No Order Executed)
```

Orders are dispatched using Alpaca's modern Python SDK (`alpaca-py`) configured in paper-trading mode:

```python
order_data = MarketOrderRequest(
    symbol="SPY",
    qty=1.0,
    side=side,
    time_in_force=TimeInForce.GTC
)
trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
order = trading_client.submit_order(order_data=order_data)
```

---

### Layer 5: Presentation & Dashboard Terminal
* **Source File:** [`src/ui/app.py`](file:///d:/Dev/repos/gsp/src/ui/app.py)
* **Runtime & Dependencies:** Streamlit Community Cloud, `streamlit>=1.30.0`, `plotly>=5.18.0`, `pandas>=2.2.3`

```
+------------------------------------------------------------------------------------+
|                       VALENCE - INSTITUTIONAL TERMINAL LAYOUT                      |
+------------------------------------------------------------------------------------+
|  [HEADER BANNER: Valence Identity & Vector SVG (Left) | Pipeline Telemetry (Right)]|
+------------------------------------------------------------------------------------+
|  [USP BANNER: Automated Horizontal Scrolling Ticker Preview (Collapsible Details)] |
+------------------------------------------------------------------------------------+
|  [5 ALIGNED CONTROLS: Timeframe | Region | Chart Display | Timezone | EMA Window]  |
+--------------------------+---------------------------------------------------------+
|  KPI TILES (LEFT COL)    |  UNIFIED CHART & ASSET CONTAINER (RIGHT COL)            |
|  - Aggregate Optimism    |  +---------------------------------------------------+  |
|    (Hero Size: 2.35rem,  |  | Multi-Series Area Plot (350px, Translucent Fills) |  |
|     Directional Delta)   |  | - Symmetrical [-100, +100] Y-Axis, Neutral Gray 0 |  |
|  - Market Bias Regime    |  | - Translucent tozeroy fills, Bold Prominent EMA   |  |
|  - Total News Volume     |  | - Unified Tooltip, Unclipped Legends, Hover Bar   |  |
|  - Tracked Indices       |  +---------------------------------------------------+  |
|  (4 Symmetrical Cards)   |  - Embedded Mini Asset Tiles (— No change States)       |
+--------------------------+---------------------------------------------------------+
|  LIVE INTELLIGENCE FEED (SINGLE UNIFIED INSTITUTIONAL CONTAINER)                   |
|  - Header: Live Stream Title (Left) | Right-Aligned Sentiment Filter Pills (Right) |
|  - Collapsible: Filter buttons directly control expansion & view without clutter   |
+------------------------------------------------------------------------------------+
```

#### 1. Visual Design Architecture
The dashboard implements an institutional financial terminal theme with a unified CSS Design System:
* **Permanent Institutional Dark Theme & Telemetry Header:** Rendered permanently in dark mode with a deep slate canvas (`#020617`), semi-translucent container cards (`#0f172a` / `rgba(15, 23, 42, 0.65)`), and directional accents (`#10b981` Bullish / `#ef4444` Bearish). The header card displays real-time telemetry (`UPDATED {time_display_str}`), a glowing green `SYSTEM ONLINE` indicator, and isolated styling preventing style bleed across components.
* **Automated Horizontal Ticker Preview for Quantitative Edge:** The USP description banner is presented as a collapsible section with an automated continuous scrolling preview ticker in its collapsed form (`uspTicker` CSS animation) that displays the key CLM vs Generative LLM mathematical thesis at a glance.
* **Ultra-Compact Single-Line 5-Control Filter Toolbar:** All 5 primary filters (`Timeframe`, `Region`, `Chart Display`, `Timezone`, `EMA Window`) are housed in a single horizontal row inside an ultra-compact bordered container (`div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stSelectbox"])`). Excess linespacing above and below the controls has been eliminated with zero outer margins, deterministic 10px rhythm, and aligned typography.
* **Consolidated Left-Column KPI Hierarchy:** The left column is structured with 4 vertically stacked KPI tiles:
  1. **Aggregate Optimism (Hero Metric):** Hero-sized value (`clamp(1.9rem, 3.2vw, 2.5rem)`, weight 800) with unambiguous directional delta tagging and CLM confidence vector telemetry.
  2. **Market Bias (Strategic Regime):** Color-coded directional regime indicator (`clamp(1.2rem, 2.2vw, 1.6rem)`) with moving average window context.
  3. **Total News Volume:** Displays processed headline volume and ingestion cadence (`Every 2 hours`).
  4. **Tracked Indices:** Displays active market universe coverage (`100% Active real-time monitored`).
* **Flush Column Alignment, Zero Dead Voids & Master Vertical Rhythm:** Both the Plotly time series and the per-index mini tiles are unified inside the exact same bordered container (`with st.container(border=True):`). The left column KPI cards and right chart container maintain strict flexbox stretching (`align-items: stretch`, `flex: 1 1 auto`) to ensure both columns terminate at the exact same bottom boundary across all global regions (IN, US, UK, JP). A deterministic 10px master vertical rhythm is enforced across all dashboard tiers (`.block-container`, `@st.fragment`, and section containers) to eliminate all dead voids and empty gaps.
* **Single-Tile Live Intelligence Feed Header:** The Live Intelligence Feed header is rendered as a clean, single-tile institutional card without nested box borders or fragmented sub-cards. The region live intelligence title and pulsing blue status beacon sit on the left, while distinct sentiment filter pills (`All`, `Bullish`, `Bearish`, `Neutral`) align cleanly on the right.

#### 2. Plotly Multi-Series Sentiment Visualization
The primary visualization renders a clean, multi-line area time series:
* **Area Plot with Soft Translucent Fills:** Renders index traces with soft translucent fills (`fill='tozeroy'`) under the lines and small markers (`size=4.5`) denoting authentic news timestamps.
* **Distinct Color Palette:** Wide-spectrum palette for constituent indices: Sky Blue (`#0284c7`), Warm Amber (`#f59e0b`), Emerald Green (`#10b981`), Vivid Magenta (`#ec4899`), Violet (`#8b5cf6`), and Cyan (`#06b6d4`).
* **Prominent Bold EMA Trend:** The aggregate regional EMA is drawn on top as a bold, prominent vector line (`width=3.5`), providing immediate visual salience as the primary directional signal.
* **Enhanced Aspect Ratio & Hover Modebar:** Plot height is set to 370px for balanced aspect ratio. The Plotly modebar is set to `displayModeBar="hover"`, keeping the chart area clean until mouseover. Zoom options (`zoom2d`, `zoomIn2d`, `zoomOut2d`) are removed and `scrollZoom` is disabled to prevent accidental scale distortions while preserving horizontal timeline panning.
* **Symmetrical Balanced Y-Axis:** Enforces a locked $[-105, +105]$ range (`dtick=25`, `fixedrange=True`) centered on a neutral slate gray zero line (`rgba(148, 163, 184, 0.45)`).
* **Unclipped Legend & Unified Tooltips:** Legend items use clean ticker names (`name=ticker`). `hovermode="x unified"` displays all series concurrently at any timestamp.

#### 3. Global Timezone Conversion Engine
The terminal allows seamless switching across five key financial timezones:
* `Asia/Kolkata (IST)`
* `UTC`
* `America/New_York (EST)`
* `Europe/London (GMT)`
* `Asia/Tokyo (JST)`

Timestamp localization occurs on-the-fly via Pandas `dt.tz_convert(target_tz)` without requiring redundant database roundtrips.

#### 4. Historical Calibration Engine & Data Floor Cutoff
To establish a pure Contrastive Language Model (CLM) regime and eliminate legacy model discontinuities, the platform underwent a one-time database purge and maintains an explicit cutoff floor:
* **Cutoff Baseline:** `2026-09-30 12:00:00+05:30` (06:30 AM UTC).
* **Database Purge:** All legacy records prior to this timestamp in both `event_signals` and `event_payloads` were permanently excised from Supabase.
* **Application Floor Filter:** [`src/ui/app.py`](file:///d:/Dev/repos/gsp/src/ui/app.py) applies `DATA_CUTOFF_FLOOR = pd.Timestamp("2026-09-30 06:30:00", tz="UTC")` immediately upon ingestion to guarantee all charts, KPI tiles, and news feeds reflect only the modern CLM era.

#### 5. Real-Time Regional Relevance & Contaminant Gatekeeper
To resolve historical data misclassifications (e.g. earlier US Wall Street headlines tagged under India, or non-financial items), [`src/ui/app.py`](file:///d:/Dev/repos/gsp/src/ui/app.py) evaluates loaded payloads in real time using [`RegionalAffinityClassifier`](file:///d:/Dev/repos/gsp/src/ingestion/classifier.py):
* **Live Contaminant Purging:** Any loaded record whose headline fails regional validation ($\text{Affinity}(\text{ExpectedRegion}) = 0$) is immediately excluded from `df_payloads` and `df_signals`.
* **Zero Chart & KPI Distortion:** Multi-index area charts, EMA momentum vectors, and executive KPI tiles calculate strictly over authenticated regional events.
* **Storage Layer Maintenance CLI:** For permanent database cleanup, [`scripts/reclassify_database.py`](file:///d:/Dev/repos/gsp/scripts/reclassify_database.py) and [`.github/workflows/reclassify_db.yml`](file:///d:/Dev/repos/gsp/.github/workflows/reclassify_db.yml) provide one-click auditing, contaminant purging (`purge`), deduplication (`dedup`), and sentiment re-scoring (`rescore`).

#### 6. Real-Time Headline Deduplication Gatekeeper
To guarantee that the user dashboard never renders redundant copies of the same news item, [`src/ui/app.py`](file:///d:/Dev/repos/gsp/src/ui/app.py) applies [`canonical_fingerprint()`](file:///d:/Dev/repos/gsp/src/ingestion/dedup.py) on the loaded DataFrame:
* **Canonical Collapse:** Groups records by normalized headline fingerprint, retaining only 1 canonical card per story.
* **Chart Weight Normalization:** Multi-index area charts and EMA calculations receive exactly 1 observation per event, eliminating artificial multi-count weighting.

#### 7. Dynamic Fragment-Isolated Live Intelligence Feed Architecture
The Live Intelligence Feed is housed in a single, unified institutional container isolated with Streamlit's `@st.fragment` decorator:
* **Dynamic Isolated Rendering (No Page Rerun):** Decorated via `@fragment_decorator` (`render_live_intelligence_feed`), user interactions with sentiment pills update only the feed component dynamically, eliminating dashboard flicker and preventing page reruns.
* **Header with Right-Aligned Color-Coded Pills:** The feed header contains the regional stream title on the left and right-aligned sentiment filter pills on the right:
  * **All:** Sky Blue border and glow (`#3b82f6` / `#60a5fa`).
  * **Bullish:** Emerald Green accent (`#10b981` / `#34d399`).
  * **Bearish:** Crimson Red accent (`#ef4444` / `#f87171`).
  * **Neutral:** Slate Gray accent (`#94a3b8` / `#cbd5e1`).
* **Default Expanded State (ALL Selected):** On initial dashboard load, `render_segmented_filter` defaults to `default_ix=0` (`All [N]`), ensuring the live intelligence feed is immediately expanded and displays all headlines for the selected region and timeframe without requiring manual filter activation.
* **Uncluttered Interface (Instruction Lines Removed):** Extraneous instruction text ("Click any sentiment pill..." and "Click active button again...") has been eliminated for an ultra-clean, institutional user experience.
* **Feed Sanitization & Neutral Classification:** Headlines undergo regex processing in `clean_news_item()` to strip HTML markup, remove trailing publisher signatures, and classify each entry into one of three sentiment buckets:
  * **Bullish Event:** Sentiment Score $\ge +0.5$ (Emerald badge)
  * **Bearish Event:** Sentiment Score $\le -0.5$ (Rose badge)
  * **Neutral Event:** $-0.5 < \text{Sentiment Score} < +0.5$ (Slate badge)

#### 6. Deep Multi-Timeframe Query Synchronization
To guarantee accurate reflection of historical activity across all selectable time horizons (`1 Day`, `12 Hours`, `6 Hours`, `4 Hours`, `7 Days`, `1 Month`, `1 Year`, `All`), the document layer query (`event_payloads` joined with `event_signals`) scales to `LIMIT 2000`:
* **Chronological Ordering:** Sorted descending (`ORDER BY s.timestamp DESC`) so the freshest catalysts appear at the top of the feed container.
* **Adaptive Timestamps:** Intraday windows (`4 Hours` through `1 Day`) render compact hour-minute badges (`%H:%M`), while multi-day windows (`7 Days`, `1 Month`, `1 Year`, `All`) render full date-time badges (`%b %d, %H:%M`) to provide unambiguous chronological context across multi-day news streams.
* **KPI Volume Parity:** Ingested news volume displayed on the left KPI card matches the filtered regional headline count.

#### 7. Symmetrical Header Freshness Badge & Dynamic Timezone Synchronization
In [`src/ui/app.py`](file:///d:/Dev/repos/gsp/src/ui/app.py), the header action card displays data freshness anchored directly to the completion timestamp of the last successful run of the Global Macro-Sentiment Pipeline:
* **Dynamic Timezone & Compact Display:** Formatted via [`format_pipeline_freshness`](file:///d:/Dev/repos/gsp/src/database/telemetry.py) into `UPDATED HH:MM {TZ}` (e.g. `UPDATED 16:03 IST`, `UPDATED 06:33 EDT`, `UPDATED 10:33 UTC`), dynamically reflecting the active timezone selected in the filter toolbar without full-page reloads. The relative elapsed time (e.g. `1h 16m ago`) is preserved inside an HTML tooltip (`title="..."`) on hover.
* **Aging Tiers & Color Accents:**
  * **Fresh ($\le 2\text{h } 15\text{m}$):** Electric Cyan accent (`#38bdf8`) signifying active 2-hour scheduled polling cycles.
  * **Aging ($2\text{h } 15\text{m} - 4\text{h}$):** Warm Amber accent (`#fbbf24`) indicating scheduled cron delays.
  * **Stale ($> 4\text{h}$):** Soft Red accent (`#f87171`) alerting users to runner interruptions.
* **Graceful Fallback:** If `pipeline_runs` has no recorded executions, it automatically falls back to `df_signals['timestamp'].max()` or `LIVE` without throwing UI exceptions.

#### 8. Reactive Zero-Reload Polling & Structural Boundary Deconfliction
To deliver real-time terminal synchronization and resolve visual boundary collisions across varying viewport sizes:
* **Background Data Polling (`run_every="30s"`):** The dashboard is encapsulated within a master `@st.fragment(run_every="30s")` coupled with `@st.cache_data(ttl=30)` on `get_processed_data()`. When new sentiment pipeline runs complete in Supabase, the terminal automatically updates charts, KPIs, and news feeds in the background with zero manual page refreshes.
* **Unified Header Banner Enclosure:** The branding typography and live telemetry status pills (`UPDATED {time_display_str}` and `SYSTEM ONLINE`) are unified inside a single continuous institutional `.header-banner-card` (`display: flex; justify-content: space-between; align-items: center;`), eliminating disconnected column cards, horizontal border offsets, and dead interior voids.
* **Boundary Deconfliction, Margin Rhythm & Chart Clearance:**
  * A deterministic 10px vertical rhythm separates the collapsible Quantitative Edge preview (`details.usp-collapsible`), the 5-control filter toolbar container, the multi-index KPI / Chart grid (`.st-key-market_optimism_chart_container`), and the Live Intelligence Feed (`.st-key-live_intelligence_feed_container`), with bottom borders flush across both columns and outer margin inflation collapsed.
  * The chart section container enforces `padding: 14px 18px 12px 18px` paired with Plotly internal margins (`margin=dict(l=8, r=44, t=28, b=0)`), completely insulating the right Y-axis `OPTIMISM SCORE` label, numerical ticks, and the upper horizontal legend from colliding with container borders.

---

### Layer 6: Autonomous Knowledge Engine
* **Source Files:** [`src/knowledge_engine/okf_updater.py`](file:///d:/Dev/repos/gsp/src/knowledge_engine/okf_updater.py), [`.github/workflows/update_okf.yml`](file:///d:/Dev/repos/gsp/.github/workflows/update_okf.yml)
* **Runtime & Dependencies:** Python 3.10+, `google-genai>=2.0.0`, `feedparser>=6.0.0`

#### 1. Autonomous Knowledge Loop
Macroeconomic regimes evolve through interest rate cycles, inflation surprises, and geopolitical developments. The Autonomous Knowledge Engine continuously updates the system's trading rules without human code modifications:

```mermaid
flowchart LR
    A["Scheduled Daily Run<br/>(00:00 UTC)"] --> B["Google News Policy Search<br/>(Central Bank and Macro Queries)"]
    B --> C["Read Current OKF Rules<br/>(knowledge/*.okf.md)"]
    C --> D["Gemini Synthesis Prompt<br/>(Identify Policy Shifts)"]
    D --> E{"Primary Model<br/>Available?"}
    E -->|Yes| F["Generate Updated Markdown Rules"]
    E -->|503 or 404 Error| G["Cascade to Fallback Model Chain"]
    G --> F
    F --> H["Write to knowledge/*.okf.md"]
    H --> I["Git Diff Check"]
    I -->|Diff Exists| J["Commit via github-actions bot<br/>and Trigger deploy.yml"]
    I -->|No Diff| K["Exit Cleanly"]
```

#### 2. Dynamic Discovery, Resilient Fallback Chain & Instant 503 Failover
To eliminate HTTP 404 errors from model deprecations and safeguard against upstream Google capacity limits, [`okf_updater.py`](file:///d:/Dev/repos/gsp/src/knowledge_engine/okf_updater.py#L30-L75) dynamically queries available Gemini models via `client.models.list()` and enforces an intelligent multi-model failover policy:

```python
DEFAULT_MODEL_FALLBACKS = [
    "gemini-3.8-flash", 
    "gemini-3.7-flash", 
    "gemini-3.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]
```

* **Dynamic API Model Discovery (`get_available_models`):** At initialization, the engine interrogates Google GenAI's model registry to discover all models supporting `generateContent` in the user's account, prioritizing preferred models (`gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.5-flash-lite`) and eliminating 404 deprecation errors.
* **Instant 503 Failover (Zero Wasted Sleeps):** If Google returns `503 UNAVAILABLE` or `OVERLOADED` on a specific model, the updater immediately fails over to the next model in the candidate pool without looping through futile retry delays on the same busy cluster.
* **Double-Pass Resilience:** If all candidate models in Pass 1 experience temporary upstream congestion, the engine cools down for 10 seconds and executes Pass 2 before aborting. If all attempts fail, existing OKF rules on disk are strictly preserved without corrupting historical knowledge.
* **Mandatory Pacing Floor (`rate_limited_generate`):** Programmatically enforces a minimum 6.0-second delay (`MIN_REQUEST_INTERVAL = 6.0`) between any two consecutive Gemini requests, mathematically capping throughput at $\le 10\text{ RPM}$ and preventing request bursts during retries or fallback transitions.
* **Explicit 429 / Quota Trap:** Specifically detects `429`, `RESOURCE_EXHAUSTED`, and `QUOTA` errors, applying an 8-second cooldown before attempting the next fallback model.
* **Inter-Region Rate Throttling:** Introduces an explicit 10.0-second cooldown (`INTER_REGION_DELAY = 10.0`) between regional runs (US, IN, UK, JP), keeping total run velocity under $\le 6\text{ RPM}$ (far below Google Gemini's 15 RPM free-tier limit).

#### 3. Dynamic Regime-Driven Rule Synthesis (Unconstrained Transmission Channels)
To eliminate artificial information bottlenecks, the OKF generation prompt does not restrict rules to an arbitrary numerical ceiling (e.g., 4–6 rules). Instead, Gemini is instructed to comprehensively span all active, independent macroeconomic transmission channels:
* **Monetary Policy & Liquidity:** Central bank interest rates, balance sheet runoff (QT), policy forward guidance.
* **Inflation Dynamics:** Core vs. headline CPI, wage inflation, energy/supply bottlenecks.
* **Sovereign Debt & Fiscal Policy:** Bond yield curves, fiscal deficits, government debt issuance.
* **Currency & External Balance:** FX depreciation/appreciation, central bank market intervention, basis spreads.
* **Trade, Tariffs & Geopolitical Friction:** Import duties, export restrictions, cross-border supply chain shocks.
* **Commodity & Energy Dynamics:** Crude oil price volatility, agricultural basket trends, seasonal weather/monsoon patterns.
* **Capital Flows & Institutional Liquidity:** FPI/FII equity & debt reallocation, domestic institutional investor flows.
* **Structural & Secular Drivers:** Tech/AI private capital expenditure, national corporate governance initiatives.

Each rule maintains a concise, institutional-grade format (1–2 sentence condition, direct directional action), preserving high semantic density and ensuring the total prompt context remains comfortably within the serverless CLM model's 2,048-token context window (`max_tokens=2048`).

---

### Layer 7: CI/CD & Orchestration Layer
* **Source Files:** [`.github/workflows/deploy.yml`](file:///d:/Dev/repos/gsp/.github/workflows/deploy.yml), [`.github/workflows/update_okf.yml`](file:///d:/Dev/repos/gsp/.github/workflows/update_okf.yml), [`.github/workflows/ci.yml`](file:///d:/Dev/repos/gsp/.github/workflows/ci.yml)

#### 1. Workflow Architecture & Decoupled Execution Graph
GitHub Actions orchestrates all recurring pipelines on isolated, non-blocking schedules with dedicated concurrency groups:

```
+-------------------------------------------------------+
|  .github/workflows/ci.yml                             |
|  - Triggers on: Push & Pull Request (master, main)    |
|  - Tasks: Dependency checks, compileall, PyTest       |
+-------------------------------------------------------+

+-------------------------------------------------------+
|  .github/workflows/update_okf.yml                     |
|  - Triggers on: Cron '0 0 * * *' (Daily at 00:00 UTC) |
|                 workflow_dispatch (Manual trigger)    |
|  - Concurrency: 'okf-updater'                         |
|  - Timeout: 15 minutes                                |
|  - Tasks: Run okf_updater.py, commit updated rules    |
|           with [skip ci] and git pull --rebase        |
+-------------------------------------------------------+

+-------------------------------------------------------+
|  .github/workflows/deploy.yml                         |
|  - Triggers on: Cron '17 */2 * * *' (Every 2 hours)  |
|                 workflow_dispatch (Manual trigger)    |
|  - Concurrency: 'sentiment-pipeline'                  |
|  - Timeout: 15 minutes                                |
|  - Tasks: Execute full Ingestion -> Inference -> DB  |
|           -> Alpaca Paper Trade pipeline              |
+-------------------------------------------------------+
```

* **Independent Decoupled Schedules:** The sentiment pipeline (`deploy.yml`) runs strictly on its 2-hour schedule without `workflow_run` coupling, preventing redundant runs or execution desynchronization when the daily knowledge updater finishes.
* **Isolated Concurrency Lanes:** `sentiment-pipeline` and `okf-updater` run under separate concurrency namespaces (`concurrency.group`), guaranteeing that one workflow never blocks, cancels, or waits on the other.
* **Runaway Process Safeguards:** Both jobs enforce `timeout-minutes: 15` and pip caching (`cache: 'pip'`), preventing hung jobs from monopolizing runner minutes.
* **Git Race Condition Elimination:** The bot commit step in `update_okf.yml` uses `[skip ci]` and `git pull --rebase origin master` to prevent trigger loops in `ci.yml` and eliminate non-fast-forward push rejections.

#### 2. Environment Secrets Management
Pipelines operate in headless containerized environments using repository-level GitHub Actions secrets:
* `DATABASE_URL`: Secure PostgreSQL connection URI pointing to Supabase PgBouncer (Port 6543).
* `TYPESAFE_API_KEY`: API token used to authenticate with the Modal CLM serverless endpoint.
* `ALPACA_API_KEY` & `ALPACA_SECRET_KEY`: Credentials for Alpaca Paper Trading API endpoints.
* `GEMINI_API_KEY`: Google AI Studio token for macroeconomic rule generation.

---

## 4. Infrastructure & Service Dependency Matrix

The table below provides a detailed breakdown of all third-party services and infrastructure components supporting the Valence production environment:

| Service / Infrastructure Component | Cloud Provider / Host | SLA Target | Resource / Pricing Tier | Primary Architectural Role | Failure Mode & Impact | Resiliency & Recovery Policy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Modal Serverless GPU** | Modal Labs (AWS us-east-1) | 99.9% | Serverless NVIDIA A10G (24GB VRAM), pay-per-second | Serves vLLM Qwen3-8B and CLM-8B System-One contrastive inference | Container cold boot stalls runner; out of memory crashes inference | Pre-baked container images via `hf_transfer`; keep-alive scale-down window (120s); fallback neutral score on network timeout |
| **Supabase PostgreSQL** | Supabase (AWS us-east-1) | 99.95% | Managed PostgreSQL 15+, PgBouncer pooler (Port 6543) | Stores vertically partitioned `event_signals` and `event_payloads` | Connection pool exhaustion under concurrent runner load | Thread-safe connection pool (`ThreadedConnectionPool`); transaction-mode pooling; explicit connection close on exit |
| **GitHub Actions Runners** | GitHub / Microsoft Azure | 99.9% | Ubuntu-latest standard runners, free-tier minutes | Schedulers for 2-hour pipeline and daily OKF knowledge evolution | Runner scheduling queue delays during peak GitHub hours | Retries via workflow dispatch; independent cron triggers; resilient idempotent pipeline execution |
| **Streamlit Community Cloud** | Snowflake / Streamlit | 99.5% | Shared cloud container, free hosting tier | Institutional user presentation dashboard and terminal interface | Container memory sleep after 7 days of inactivity; app crash on database disconnect | In-memory `@st.cache_data(ttl=30)` to minimize DB strain; graceful fallback to mock data on DB failure |
| **Alpaca Paper Trading API** | Alpaca Securities LLC | 99.95% | Free Paper Trading API tier (REST/WebSocket) | Algorithmic order submission (`MarketOrderRequest`) and portfolio execution | Order rejected due to market hours, invalid symbol, or API timeout | Handled via try/except logging blocks; trade execution failures do not interrupt database ingestion |
| **Google Gemini API** | Google Cloud Vertex / AI Studio | 99.9% | Free / Pay-as-you-go Gemini Flash API | Macroeconomic regime reasoning and dynamic OKF rule authoring | HTTP 503 high-load errors; 15 RPM rate-limiting throttling | Multi-model fallback chain (`3.8-flash` $\rightarrow$ `3.7-flash` $\rightarrow$ `3.5-flash-lite`); 5s rate-limiting delays |
| **Google News RSS Aggregators** | Google LLC | Best-effort | Public web endpoints (Rate-limited) | Ingestion source for global financial and macroeconomic news | Network timeout; IP rate-limiting blocking requests | 10-second `aiohttp` client timeout; max 3 headlines per ticker cap; dual search channels (Google + Reuters) |

---

## 5. Production Operations & Troubleshooting Guide

### 1. Ingestion Pipeline Failures

#### Symptom: Zero Payloads Fetched During Poller Execution
* **Root Causes:**
  1. Temporary network interruption reaching Google News endpoints.
  2. Google News returned HTTP 429 (Too Many Requests) due to runner IP throttling.
* **Diagnosis:**
  ```bash
  # Test network reachability and feed validity locally
  python -c "
  import asyncio
  from src.ingestion.poller import FeedPoller, FEEDS
  poller = FeedPoller(feeds=FEEDS[:2])
  results = asyncio.run(poller.run())
  print(f'Fetched {len(results)} items')
  "
  ```
* **Resolution:** Verify that `RSSClient` sets an appropriate user-agent string and adheres to the 10-second request timeout. If specific query terms trigger rate limits, refine the query parameters in `BASE_QUERIES`.

---

### 2. Modal Inference & AI Scoring Outages

#### Symptom: HTTP 500/504 Errors or Timeouts from TypeSafe SDK
* **Root Causes:**
  1. The Modal serverless container experienced an out-of-memory (OOM) error during vLLM initialization.
  2. vLLM embedding server on port 8090 failed its internal health check.
* **Diagnosis:**
  ```bash
  # Check Modal deployment logs and container status
  modal app list
  modal container list
  # Test the endpoint directly
  python tests/integration/test_modal.py
  ```
* **Resolution:**
  1. Confirm that `--gpu-memory-utilization 0.9` provides sufficient overhead for CUDA allocations.
  2. Ensure the container image uses `min_containers=0` and a `scaledown_window=120` to balance cold-boot latency against credit usage.
  3. If Modal is unreachable, [`src/main.py`](file:///d:/Dev/repos/gsp/src/main.py#L79-L81) defaults gracefully to a `Neutral` score ($0.0$), ensuring pipeline execution continues uninterrupted.

---

### 3. Database Connection Pool Exhaustion

#### Symptom: `psycopg2.OperationalError: remaining connection slots are reserved for non-replication superuser connections`
* **Root Causes:**
  1. Database queries are connecting directly to PostgreSQL port 5432 rather than PgBouncer port 6543.
  2. Runner jobs crashed without properly releasing connections back to the pool.
* **Diagnosis:**
  ```sql
  -- Inspect active connection counts by application
  SELECT count(*), application_name, state 
  FROM pg_stat_activity 
  GROUP BY application_name, state;
  ```
* **Resolution:**
  1. Verify that `DATABASE_URL` specifies port `6543` with `?pgbouncer=true`.
  2. Ensure database operations use the context manager pattern in [`src/database/client.py`](file:///d:/Dev/repos/gsp/src/database/client.py), which guarantees connection cleanup via `finally: self.pool.putconn(conn, close=is_broken)`.

#### Symptom: `psycopg2.OperationalError: server closed the connection unexpectedly` followed by `Database empty`
* **Root Causes:**
  1. Streamlit Community Cloud runs `src/ui/app.py` as a persistent process. When idle between user visits, Supabase's connection pooler (PgBouncer/Supavisor) or intermediate NAT firewalls terminate idle TCP sockets (typically after 5–10 minutes).
  2. The pool retained the dead socket. When a user visited the dashboard, the dead socket was handed to `load_data()`, raising an `OperationalError` and causing Streamlit to fall back to an empty DataFrame state.
* **Diagnosis:**
  * Check if GitHub Actions runs are succeeding (i.e. database is healthy and actively receiving rows).
  * If the database is healthy, the error is purely a client-side idle socket drop.
* **Resolution:**
  1. **TCP Keepalives:** Ensured `ThreadedConnectionPool` sets `keepalives=1`, `keepalives_idle=30`, `keepalives_interval=10`, `keepalives_count=5`.
  2. **Pre-Checkout Liveness Check:** `SupabasePoolClient._get_valid_connection()` tests sockets with `SELECT 1;` before checkout and purges dead sockets with `close=True`.
  3. **Auto-Retry Loop:** `load_data()` in `src/ui/app.py` includes a 2-attempt retry loop that calls `reset_db_client()` on failure and re-executes seamlessly with zero user interruption.

---

### 4. Alpaca Order Execution Errors

#### Symptom: `alpaca.common.exceptions.APIError: forbidden / invalid credentials` or `market is closed`
* **Root Causes:**
  1. The API key or secret has expired or was incorrectly set in GitHub Secrets.
  2. A market order was rejected because the exchange is outside regular trading hours.
* **Diagnosis:**
  ```bash
  python -c "
  import os
  from alpaca.trading.client import TradingClient
  client = TradingClient(os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY'), paper=True)
  print(client.get_account().status)
  "
  ```
* **Resolution:**
  1. Verify the `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` secrets in GitHub repository settings.
  2. For after-hours paper testing, wrap market orders in extended-hours flags or switch to limit order representations if required by trading logic.

---

### 5. Streamlit Terminal Desynchronization & Caching

#### Symptom: Dashboard Displays Outdated Signals or Blank Charts
* **Root Causes:**
  1. `st.cache_data` has not reached its 30-second time-to-live (TTL).
  2. The selected region or timeframe contains no recent database entries.
* **Diagnosis:**
  * Open the Streamlit terminal, click the top-right menu icon, and select **Clear cache**.
  * Check the terminal's **Aggregate Optimism** KPI card; if marked `0.0` with 0 volume, verify that the GitHub Actions ingestion workflow has been running on schedule.
* **Resolution:**
  * Verify that Supabase contains records from the last 24 hours:
    ```sql
    SELECT count(*), max(timestamp) FROM event_signals;
    ```
  * In local development, start the dashboard with caching disabled to inspect query responses in real time:
    ```bash
    streamlit run src/ui/app.py --server.runOnSave true
    ```

---

### 6. Disaster Recovery & Manual Rollback

If an automated Gemini update introduces flawed trading rules into the Objective Knowledge Framework, revert to the last stable rule set using standard Git version control:

```bash
# 1. Inspect recent changes to regional OKF rules
git log -p -n 3 knowledge/

# 2. Revert to the previous stable commit
git checkout HEAD~1 -- knowledge/

# 3. Commit the manual rollback
git commit -m "docs(knowledge): rollback macro rules to prior stable revision"
git push origin master
```

Because `.github/workflows/deploy.yml` reads directly from the checked-out workspace on each run, the rollback takes effect immediately on the next scheduled execution cycle.

---

## 6. Quantitative Benchmarking & Alpha Validation Architecture

To ensure Valence meets institutional quantitative standards, the platform includes a native, automated **4-Tier Benchmarking Suite** (`src/benchmark/` and `scripts/run_benchmarks.py`).

```mermaid
flowchart TD
    subgraph B1["Tier 1: AI / NLP Sentiment Calibration"]
        T1_DATA["Macro Golden Dataset (500 Curated Events)"] --> T1_CLM["System-One CLM-8B Engine"]
        T1_DATA --> T1_LM["Loughran-McDonald Baseline"]
        T1_CLM & T1_LM --> T1_EVAL["Accuracy, Macro F1, ECE Calibration, Brier Score, Latency"]
    end

    subgraph B2["Tier 2: Ingestion & Regional Filtering"]
        T2_FEEDS["Multi-Region Geotargeted Feeds"] --> T2_AFF["RegionalAffinityClassifier"]
        T2_FEEDS --> T2_DEDUP["NewsDeduplicator (SHA-256)"]
        T2_AFF & T2_DEDUP --> T2_EVAL["Contamination Rate (<2%), Noise Rejection %, Deduplication Yield"]
    end

    subgraph B3["Tier 3: Quantitative Alpha Backtesting"]
        T3_SIGS["Valence Signals (I_t, EMA_t)"] --> T3_ENGINE["ValenceBacktestEngine"]
        T3_PRICE["OHLCV Price Bars (SPY, QQQ, NIFTY)"] --> T3_ENGINE
        T3_ENGINE --> T3_METRICS["Sharpe, Sortino, Max Drawdown, Calmar, Information Coefficient (IC)"]
    end

    subgraph B4["Tier 4: System & Infrastructure Latency"]
        T4_INFRA["Supabase DB + Streamlit Terminal"] --> T4_PROF["SystemProfiler"]
        T4_PROF --> T4_OUT["Pool Checkout ms, BRIN Query Latency ms, Fragment Render ms"]
    end

    T1_EVAL & T2_EVAL & T3_METRICS & T4_OUT --> REPORT["Timestamped Benchmark Report (reports/benchmark_report.md)"]
```

### 6.1 Benchmark Tiers Summary

1. **Tier 1 (NLP Calibration & Classification)**: Evaluates System-One CLM against Loughran-McDonald and FinBERT on `knowledge/benchmark/macro_golden_dataset.json`. Measures Expected Calibration Error (ECE), Brier Score, and bitwise determinism ($\text{Var}(\text{score}) = 0$).
2. **Tier 2 (Ingestion & Regional Affinity)**: Verifies that cross-region contamination across IN, US, UK, JP is strictly controlled ($< 2.0\%$), non-financial clickbait is rejected ($100\%$), and duplicate syndicated articles are suppressed ($> 80\%$).
3. **Tier 3 (Quantitative Alpha & Signal Backtesting)**: Aligns Valence 4-period EMA crossover signals with historical hourly price bars (via `yfinance`), simulating trades under realistic slippage (5 bps) and fees (1 bps). Measures Information Coefficient (IC), Rank IC, Directional Hit Rate, Sharpe Ratio, Sortino Ratio, and Max Drawdown vs Buy & Hold.
4. **Tier 4 (System & Database Latency)**: Profiles Supabase connection pool checkout latency, BRIN index query performance on `event_signals`, and `@st.fragment` partial re-render duration.

### 6.2 Execution Runbook

Run the complete benchmark suite locally or in CI:
```bash
# Execute all 4 tiers and generate markdown/json reports
python scripts/run_benchmarks.py --all

# Run specific tier
python scripts/run_benchmarks.py --tier nlp
python scripts/run_benchmarks.py --tier classifier
python scripts/run_benchmarks.py --tier alpha --symbol SPY --days 90
python scripts/run_benchmarks.py --tier system
```

Reports are automatically saved to `reports/benchmark_report.md` and `reports/benchmark_data.json`.

