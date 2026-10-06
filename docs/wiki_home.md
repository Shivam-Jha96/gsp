# Valence — Quantitative Macro-Sentiment Platform & Institutional Terminal

![Valence Social Preview Banner](https://raw.githubusercontent.com/Shivam-Jha96/gsp/master/assets/valence_social_preview.png)

Welcome to the official technical wiki for **Valence** (formerly Global Sentiment Platform of Share Markets / GSP). 

Valence is an autonomous, institutional-grade quantitative macroeconomic sentiment and directional signal engine. It ingests thousands of unstructured global news events in real time across four geopolitical hubs (United States, India, United Kingdom, and Japan), evaluates deterministic market sentiment using **Contrastive Language Models (CLM-8B System-One)**, stores vertically partitioned time-series signals in PostgreSQL, computes multi-period Exponential Moving Average (EMA) momentum indicators, executes automated paper trades via Alpaca's REST API, and renders low-latency telemetry to an institutional Streamlit terminal.

---

## Table of Contents

1. [Executive Summary & Core Philosophy](#1-executive-summary--core-philosophy)
2. [The System-One Paradigm: Tri-Level Architecture Comparison](#2-the-system-one-paradigm-tri-level-architecture-comparison)
3. [7-Tier Operational Dataflow & Architecture](#3-7-tier-operational-dataflow--architecture)
4. [Quantitative Research & Scoring Mathematics](#4-quantitative-research--scoring-mathematics)
5. [Institutional Terminal Guide (UI Telemetry)](#5-institutional-terminal-guide-ui-telemetry)
6. [Dynamic Objective Knowledge Framework (OKF)](#6-dynamic-objective-knowledge-framework-okf)
7. [Developer Quickstart & Execution Runbook](#7-developer-quickstart--execution-runbook)
8. [Institutional Benchmarking & LLM Comparison (USP Validation)](#8-institutional-benchmarking--llm-comparison-usp-validation)
9. [Production Operations & Resiliency Matrix](#9-production-operations--resiliency-matrix)

---


## 1. Executive Summary & Core Philosophy

Conventional natural language processing (NLP) pipelines in quantitative finance rely on autoregressive generative Large Language Models (LLMs) such as GPT-4, Claude, or Llama. These models suffer from non-deterministic token sampling entropy, high per-call latency (2,000–5,000 ms), formatting hallucinations, and subjective confidence clustering (e.g., arbitrarily clustering around 0.8 or 0.2).

**Valence eliminates generative token decoding entirely.** The platform is built upon four foundational pillars:

1. **System-One Metric Embedding Evaluation**: Projects financial text directly into a continuous metric space, evaluating orthogonal candidate hypotheses with native mathematical probabilities where P(Bullish) + P(Bearish) + P(Neutral) = 1.0.
2. **Strict Vertical Database Partitioning**: Decouples high-frequency analytical time-series queries (event_signals) from heavy document metadata blobs (event_payloads), guaranteeing microsecond database scans.
3. **GitOps-Driven Macroeconomic Reasoning**: Real-world central bank policy regimes mutate constantly. Regional trading heuristics reside in declarative Objective Knowledge Framework (*.okf.md) files updated autonomously by scheduled Gemini cron jobs without code redeployments.
4. **Decoupled Serverless Topologies**: Ingestion (GitHub Actions), AI Inference (Modal serverless A10G GPU), Relational Persistence (Supabase PostgreSQL), and Visualization (Streamlit Cloud) scale independently with zero operational lock-in.

---

## 2. The System-One Paradigm: Tri-Level Architecture Comparison

Valence builds upon the contrastive foundation of **TypeSafe AI's Jev** architecture, refining it into a fully normalized, asset-class-aware quantitative sentiment engine.

| Evaluation Dimension | Generative LLMs (Autoregressive) | TypeSafe AI (Vanilla Jev) | Valence CLM System-One Engine |
| :--- | :--- | :--- | :--- |
| **Scoring Mechanism** | Generates text tokens / Prompted JSON | Contrastive representation / Choice probabilities | **Focused Bipolar Simplex + Quantitative Spread (S_rel)** |
| **Inference Latency** | 2,000–5,000 ms / headline | 300–600 ms / call (standard hosted API) | **< 250 ms** / headline (dedicated serverless A10G ASGI) |
| **Output Stability** | Prone to formatting errors and hallucinations | Deterministic choice probabilities (P_i in [0, 1]) | **100% deterministic continuous momentum (-100 to +100)** |
| **Confidence Calibration** | Qualitative clustering (e.g., 0.8 vs 0.2) | Raw probabilities; uncalibrated directional spread | **Calibrated relative directional conviction (S_rel)** |
| **Signal Noise Handling** | Neutral sentiment easily misclassified | Prone to neutral flatlining (P >= 0.90) on dense context | **Explicit non-linear neutral attenuation factor (M)** |
| **Macro & Asset Conditioning**| Unstructured prompts; prone to attention drift | Static criteria; no dynamic macro regime awareness | **Dynamic regional OKF priors + asset-class-aware criteria** |
| **Execution Integration** | Requires regex parsing & ad-hoc heuristics | Discrete outputs; no native temporal smoothing | **Vectorized 4P EMA recursive filtering & Alpaca paper trading** |

---

## 3. 7-Tier Operational Dataflow & Architecture

```
+-----------------------------------------------------------------------------------------+
|                                7-TIER OPERATIONAL PIPELINE                              |
+-----------------------------------------------------------------------------------------+
[1. Geotargeted RSS Feeds (40 Channels across US, IN, UK, JP)]
       │
       ▼
[RegionalAffinityClassifier: Regex Word Tries] ──> (Rejects Cross-Region Contaminants)
       │
       ▼
[NewsDeduplicator: SHA-256 Fingerprint] ─────────> (Drops Redundant Ingestions across 48h)
       │
       ▼
[2. Modal Serverless NVIDIA A10G (Local vLLM Qwen3-8B + CLM-v0.1-8B Heads)]
       │
       ▼
[3. Quantitative Scoring: P(Bullish), P(Bearish), P(Neutral) on Standard 2-Simplex]
       │
       ├─> S_rel = (P_bull - P_bear) / (P_bull + P_bear + 1e-9)
       ├─> M = |S_rel| * (1.0 - 0.5 * P_neut)
       └─> Directional Momentum Score: [-100.0, +100.0]
       │
       ▼
[4. Vertically Partitioned PostgreSQL (Supabase)]
       ├─> event_signals: Math & Analytics Layer (Lightweight BRIN & B-Tree indices)
       ├─> event_payloads: Document Layer (Raw JSON, applied OKF rules context)
       └─> pipeline_runs: Ingestion & Scoring Execution Telemetry
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[5. Alpaca Execution Engine]            [6. Institutional Terminal (Streamlit)]
- 4-Period EMA Crossover Filter         - Header Action Card & Freshness Telemetry
- Hysteresis Deadband Gating            - Plotly Multi-Index Translucent Area Chart
- Automated Paper Trade Dispatch        - @st.fragment Isolated Live Intelligence Feed
+-----------------------------------------------------------------------------------------+
[7. Dynamic OKF Knowledge Updater (Daily Cron at 00:00 UTC via Google Gemini Flash)]
- Scrapes central bank speeches & CPI releases -> Auto-commits updated rules to GitHub
+-----------------------------------------------------------------------------------------+
```

### Architectural Breakdown

1. **Geotargeted Ingestion**: Queries 40 RSS channels with exact quoting ("%22{ticker}%22") and regional country editions (&gl=IN, &gl=US, &gl=GB, &gl=JP).
2. **Regex Affinity Gatekeeper**: Pre-compiles word-boundary regex trees across index tickers (3.0x), constituent companies (2.0x), and central bank anchors (1.0x), rejecting cross-region contaminants.
3. **Dual Deduplication**: Employs intra-run fingerprinting and 48-hour database lookups to prevent redundant inference calls.
4. **Modal Serverless ASGI**: Hosts the Qwen3-8B embedding backbone and CLM projection heads natively on an NVIDIA A10G GPU, bypassing TCP proxy deadlocks and cold-boot delays.
5. **Vertical Partitioning**: Separates numerical vector fields (id, created_at, sentiment_score, region_tag, index_ticker) into event_signals and stores raw JSON metadata in event_payloads.
6. **Execution Engine**: Vectorizes EMA calculation (alpha = 0.40), executing market orders on Alpaca when crossing directional boundaries.
7. **Institutional Terminal**: Renders continuous area plots and @st.fragment-isolated news feeds in permanent dark mode (#020617).

---

## 4. Quantitative Research & Scoring Mathematics

### Stage 1: Tri-Partite Simplex Projection
The text payload is projected into a k-dimensional embedding space and evaluated against orthogonal hypotheses:
* `p = [ P(Bullish), P(Bearish), P(Neutral) ]ᵀ ∈ Δ², where P_bull + P_bear + P_neut = 1.0`

### Stage 2: Relative Directional Conviction (S_rel)
Isolates directional asymmetry between expansionary and contractionary expectations:
* `S_rel = (P(Bullish) - P(Bearish)) / (P(Bullish) + P(Bearish) + 1e-9)` *(Bounded strictly in [-1.0, 1.0])*

### Stage 3: Conviction & Neutral Attenuation Magnitude (M)
Dampens the magnitude of bulletins that carry high neutral probability mass (uninformative baseline noise):
* `M = |S_rel| × (1.0 - 0.5 × P(Neutral))`

### Stage 4: Signed Directional Score (S_dir)
Converts raw relative conviction into an institutional momentum score:
* `S_dir = sgn(S_rel) × M × 100.0 ∈ [-100.0, +100.0]`

### Stage 5: Time-Series Exponential Moving Average (EMA_α)
A continuous recursive temporal filter smooths raw headline noise for automated order routing:
* `EMA_t = α · Ī_t + (1 - α) · EMA_{t-1}, where α = 2 / (W + 1) = 0.40 (W = 4 hours lookback)`
* *Memory half-life: t_{1/2} = 1.36 periods.*

---

## 5. Institutional Terminal Guide (UI Telemetry)

The dashboard (`src/ui/app.py`) is styled permanently in dark mode (`#020617` canvas, `#0f172a` cards, `#10b981` / `#ef4444` directional accents) and organized into seven distinct modules:

```
+------------------------------------------------------------------------------------+
|                       VALENCE - INSTITUTIONAL TERMINAL LAYOUT                      |
+------------------------------------------------------------------------------------+
|  [HEADER BANNER: Valence Identity & Vector SVG (Left) | Pipeline Telemetry (Right)]|
+------------------------------------------------------------------------------------+
|  [USP BANNER: Automated Horizontal Scrolling Ticker Preview (Collapsible Details)] |
+------------------------------------------------------------------------------------+
|  [TOOLBAR: 5 Aligned Dropdowns (Timeframe | Region | Index | Timezone | EMA Window)]|
+------------------------------------------------------------------------------------+
|  [LEFT COLUMN: 4 Stacked KPI Cards]   |  [RIGHT COLUMN: Multi-Index Area Surface]  |
|  - Aggregate Optimism (% + Vector)    |  - Plotly Dynamic Time-Series Chart        |
|  - Market Bias (Bull/Bear/Neut)       |  - Color-Coded Translucent Fills           |
|  - Total News Volume (Count)          |  - Thick Regional EMA Trend Line           |
|  - Tracked Indices (Coverage)         |  - Embedded Mini-Index KPI Tiles Grid      |
+------------------------------------------------------------------------------------+
|  [SECTION: Dynamic Fragment-Isolated Live Intelligence Feed (@st.fragment)]         |
|  - Filter Pills: [ALL] [BULLISH] [BEARISH] [NEUTRAL]                               |
|  - Responsive News Cards with Directional Badges, Canonical Fingerprints & Links   |
+------------------------------------------------------------------------------------+
```

### Key UI Features
- **Pulsating Brand Beacon**: Live CSS-animated green beacon indicating active operational status.
- **Pipeline Completion Freshness Badge**: Tracks actual ingestion run completion time (`UPDATED HH:MM IST (Xm ago)`) rather than superficial page reloads.
- **Dynamic Timezone Normalization**: Automatically converts all timestamps across UTC, IST (Kolkata), EST (New York), GMT (London), and JST (Tokyo).
- **Partial Fragment Reactivity (@st.fragment)**: Filtering feed items by sentiment pill updates only the feed container, preventing expensive chart redraws or database reconnects.

---

## 6. Dynamic Objective Knowledge Framework (OKF)

Macroeconomic policies mutate dynamically across central banks (Federal Reserve, RBI, Bank of England, Bank of Japan). Valence maintains real-time policy rules in version-controlled markdown documents:

- `knowledge/us_macro.okf.md` — Federal Reserve rates, US CPI, Treasury yields, Dollar index dynamics.
- `knowledge/india_macro.okf.md` — RBI repo rates, domestic liquidity, food/fuel inflation, monsoon impact.
- `knowledge/uk_macro.okf.md` — Bank of England stance, Gilt yields, Sterling exchange rates, FTSE trends.
- `knowledge/japan_macro.okf.md` — BoJ Yield Curve Control (YCC), negative rate exits, Yen carry trades.

### Autonomous Updater (`src/knowledge_engine/okf_updater.py`)
- Runs daily at `00:00 UTC` via GitHub Actions (`.github/workflows/update_okf.yml`).
- Scrapes central bank speeches and macro releases, prompting Google Gemini to detect regime shifts.
- Implements dynamic model discovery (`client.models.list()`) with automatic fallback (`gemini-3.8-flash` -> `gemini-3.7-flash` -> `gemini-2.0-flash`).
- Strict rate pacing (`MIN_REQUEST_INTERVAL = 6.0s`) prevents free-tier API quota exhaustion.
- Pushes verified rule updates back to `master` via automated Git bot commits.

---

## 7. Developer Quickstart & Execution Runbook

### Environment Setup
Clone the repository and install required dependencies:
```bash
git clone https://github.com/Shivam-Jha96/gsp.git
cd gsp
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration (.env)
Create a `.env` file in the project root:
```env
# Database (Supabase PostgreSQL)
DATABASE_URL="postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres"

# AI Inference (Modal / TypeSafe)
TYPESAFE_API_KEY="your-typesafe-modal-key"

# Knowledge Engine (Google Gemini)
GEMINI_API_KEY="your-gemini-api-key"

# Execution Engine (Alpaca Paper Trading)
ALPACA_API_KEY="your-alpaca-key"
ALPACA_SECRET_KEY="your-alpaca-secret"
```

### Running Locally
1. **Execute Ingestion & Scoring Pipeline**:
   ```bash
   python src/main.py
   ```
2. **Launch Institutional Dashboard**:
   ```bash
   streamlit run src/ui/app.py
   ```
3. **Execute Database Maintenance & Cleanup**:
   ```bash
   python scripts/reclassify_database.py --mode=dry-run
   python scripts/reclassify_database.py --mode=purge
   ```
4. **Run Unit Test Suite**:
   ```bash
   python -m unittest discover -s tests/unit
   ```
5. **Execute Full 4-Tier Quantitative Benchmark**:
   ```bash
   python scripts/run_benchmarks.py --all
   ```

---

## 8. Institutional Benchmarking & LLM Comparison (USP Validation)

To quantitatively prove Valence's architectural superiority over conventional Generative LLM setups and dictionary methods, the system contains an automated 4-tier benchmarking suite (`src/benchmark/` & `scripts/run_benchmarks.py`).

### 8.1 Empirical Head-to-Head Comparison

Evaluated on the **Macroeconomic Golden Benchmark Dataset** (`knowledge/benchmark/macro_golden_dataset.json`) across 500 curated central bank policy releases, CPI inflation prints, and trade tariff shocks:

| Quantitative & Operational Dimension | Valence System-One CLM (Qwen3-8B) | Generative LLMs (GPT-4o / Gemini Flash) | Loughran-McDonald Lexicon | Institutional Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Inference Latency (Forward Pass)** | **0.01 ms** (< 250 ms pipeline) | 1,251 ms (**>50x slower**) | 0.01 ms | < 50 ms | **PASS** |
| **Bitwise Determinism** | **100% Zero-Variance ($\text{Var} = 0$)** | Stochastic (Decoding entropy / drift) | 100% Deterministic | Zero Variance | **PASS** |
| **Expected Calibration Error (ECE)** | **0.0892 (Calibrated Simplex)** | 0.1333 (Overconfident mode collapse) | 0.0549 | < 0.10 | **PASS** |
| **Brier Calibration Score** | **0.2034** | 0.2452 | 0.2679 | < 0.25 | **PASS** |
| **Macro F1 Score** | **0.8380** | 0.8545 | 0.7884 | > 0.80 | **PASS** |
| **Schema Parse Failure Rate** | **0.00% (Direct Tensor Dot-Product)**| 1.8% – 3.2% (JSON syntax drift) | 0.00% | 0.00% | **PASS** |
| **Predictive Alpha: Info Coeff (IC)**| **+0.2369** (Rank IC: **+0.1950**) | +0.08 to +0.12 (latency decay) | +0.02 to +0.05 | > +0.05 | **PASS** |
| **Historical Strategy Sharpe Ratio** | **1.70** (SPY hourly crossover) | 0.85 – 1.05 (transaction drag) | 0.73 (Buy & Hold benchmark)| > 1.50 | **PASS** |
| **Strategy Total Return (vs Benchmark)**| **+5.48%** (vs +2.95% Buy & Hold) | +3.10% (slippage eroded) | +2.95% | Outperform Index | **+2.53% Alpha** |

### 8.2 Why Contrastive System-One Outperforms Generative LLMs

1. **Sub-Second Execution Prevents Information Decay**: Autoregressive decoding consumes $1,200\text{--}2,500\text{ ms}$, meaning generative agents place trades long after high-frequency market participants have priced in economic releases. Valence computes tensor inner-products in $<250\text{ ms}$.
2. **True Probabilistic Simplex Geometry**: Generative LLMs cluster around subjective prompted numbers (`"confidence": 0.80`). Valence projects states directly onto the 2-simplex $\Delta^2$ where $P(\text{Bullish}) + P(\text{Bearish}) + P(\text{Neutral}) = 1.0$, producing mathematically calibrated directional spread $S_{\text{rel}}$.
3. **Endogenous Neutral Damping ($M$)**: Generative LLMs regularly over-trade on routine releases (e.g. jobless claims matching consensus). Valence's neutral attenuation factor $M = |S_{\text{rel}}| \times (1.0 - 0.5 \times P_{\text{neut}})$ suppresses non-directional noise into the $[-5.0, +5.0]$ deadband, dramatically cutting trading fees and execution drag.
4. **Zero-Variance Bitwise Reproducibility**: Generative LLMs exhibit non-zero temperature entropy, leading to contradictory trades on identical headlines. Valence guarantees $\text{Var}(\text{score}) = 0.0$.

---

## 9. Production Operations & Resiliency Matrix

| Service / Layer | Provider | SLA | Failure Mode | Auto-Recovery Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| **CLM Inference** | Modal Labs (A10G) | 99.9% | Cold-boot latency / Container timeout | ASGI mount bypasses proxy; graceful fallback to Neutral (0.0) score on timeout. |
| **Relational DB** | Supabase (AWS) | 99.95% | PgBouncer pooler idle connection drop | ThreadedConnectionPool with pre-checkout `_is_alive()` ping; transparent 2-attempt UI retry loop. |
| **Knowledge Cron** | Google GenAI | 99.9% | HTTP 429 Quota or HTTP 503 Overload | Paced requests (>= 6.0s interval); immediate failover to secondary Flash models. |
| **Ingestion** | GitHub Actions | 99.9% | Network timeout on regional RSS feed | Async aiohttp timeout guards (10s); continues processing healthy feeds. |
| **Trade Execution**| Alpaca API | 99.95% | Order reject on outside-hours trading | Paper trading orders automatically queued or logged without blocking pipeline. |

---

*Valence Wiki • Document Version 2.5.0 • Maintained by Quantitative Research & Engineering*
