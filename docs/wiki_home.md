# Valence — Quantitative Macro-Sentiment Platform & Open Intelligence Terminal

<p align="center">
  <img src="https://raw.githubusercontent.com/Shivam-Jha96/gsp/master/assets/valence_social_preview.png" alt="Valence Social Preview Banner" width="100%" style="border-radius: 8px;" />
</p>


Welcome to the official technical wiki for **Valence** (formerly Global Sentiment Platform of Share Markets / GSP). 

Valence is an open-source quantitative macroeconomic sentiment and directional signal engine. It continuously ingests geopolitical and financial news events across four geopolitical hubs (United States, India, United Kingdom, and Japan), evaluates deterministic market sentiment using **Contrastive Language Models (CLM-8B System-One)**, stores vertically partitioned time-series signals in PostgreSQL, computes multi-period Exponential Moving Average (EMA) momentum indicators, evaluates directional stances for paper trading evaluation (order execution disabled in research MVP mode), and renders low-latency telemetry to a high-contrast dark Streamlit terminal.

---

## Table of Contents

1. [Executive Summary & Core Philosophy](#1-executive-summary--core-philosophy)
2. [The System-One Paradigm: Tri-Level Architecture Comparison](#2-the-system-one-paradigm-tri-level-architecture-comparison)
3. [8-Tier Operational Dataflow & Architecture](#3-8-tier-operational-dataflow--architecture)
4. [Quantitative Research & Scoring Mathematics](#4-quantitative-research--scoring-mathematics)
5. [Open Intelligence Terminal Guide (UI Telemetry)](#5-open-intelligence-terminal-guide-ui-telemetry)
6. [Dynamic Objective Knowledge Framework (OKF)](#6-dynamic-objective-knowledge-framework-okf)
7. [Empirical Benchmarking & LLM Comparison (USP Validation)](#7-empirical-benchmarking--llm-comparison-usp-validation)
8. [Production Operations & Resiliency Matrix](#8-production-operations--resiliency-matrix)
9. [Regulatory Disclaimers & Data Terms](#9-regulatory-disclaimers--data-terms)

---


## 1. Executive Summary & Core Philosophy

Conventional natural language processing (NLP) pipelines in quantitative finance rely on autoregressive generative Large Language Models (LLMs) such as GPT-4, Claude, or Llama. These models introduce non-deterministic token sampling entropy, high per-call latency (1,200–2,500 ms), formatting hallucinations, and subjective confidence clustering (e.g., arbitrarily clustering around 0.8 or 0.2).

**Valence eliminates generative token decoding entirely.** The platform is built upon four foundational pillars:

1. **System-One Metric Embedding Evaluation**: Projects financial text directly into a continuous metric space, evaluating orthogonal candidate hypotheses with native mathematical probabilities where P(Bullish) + P(Bearish) + P(Neutral) = 1.0.
2. **Strict Vertical Database Partitioning**: Decouples high-frequency analytical time-series queries (event_signals) from heavy document metadata blobs (event_payloads), guaranteeing fast indexed analytical database scans via BRIN indexes and vertical partitioning.
3. **GitOps-Driven Macroeconomic Reasoning**: Real-world central bank policy regimes mutate constantly. Regional trading heuristics reside in declarative Objective Knowledge Framework (*.okf.md) files updated autonomously by scheduled Gemini cron jobs without code redeployments.
4. **Decoupled Serverless Topologies**: Ingestion (GitHub Actions), AI Inference (Modal serverless A10G GPU running open-weights vLLM Qwen3-8B + contrastive-lm), Relational Persistence (Supabase PostgreSQL), and Visualization (Streamlit Cloud) scale independently with zero operational lock-in.

---

## 2. The System-One Paradigm: Tri-Level Architecture Comparison

Valence operates on a **100% self-hosted, sovereign contrastive inference pipeline**. It uses an open-source contrastive learning paradigm (System-One CLM-8B) running natively on a private Modal serverless GPU container (`vLLM` running `Qwen/Qwen3-8B` + `contrastive-lm` ASGI endpoint in `src/ai_engine/modal_app.py`). **Valence does not use TypeSafe or Jev's hosted cloud service or proprietary SDKs**; inference is executed via a lightweight native HTTP client ([`src/ai_engine/clm_client.py`](file:///d:/Dev/repos/gsp/src/ai_engine/clm_client.py)) communicating directly with your private Modal endpoint.

| Evaluation Dimension | Generative LLMs (Autoregressive) | Vanilla Contrastive Baseline | Valence CLM System-One Engine |
| :--- | :--- | :--- | :--- |
| **Scoring Mechanism** | Generates text tokens / Prompted JSON | Contrastive representation / Choice probabilities | **Bipolar Simplex Projection + Quantitative Spread (S_rel)** |
| **Inference Latency** | 1,200–2,500 ms / headline | 70–500 ms / call (standard hosted API) | **180–350 ms warm API / batch** (serverless A10G) |
| **Output Stability** | Prone to formatting errors and hallucinations | Deterministic choice probabilities (P_i in [0, 1]) | **Deterministic continuous momentum (-100 to +100)** |
| **Confidence Calibration** | Qualitative clustering (e.g., 0.8 vs 0.2) | Raw probabilities; uncalibrated directional spread | **Calibrated relative directional conviction (S_rel)** |
| **Signal Noise Handling** | Neutral sentiment easily misclassified | Prone to neutral flatlining (P >= 0.90) on dense context | **Explicit non-linear neutral attenuation factor (M)** |
| **Macro & Asset Conditioning**| Unstructured prompts; prone to attention drift | Static criteria; no dynamic macro regime awareness | **Dynamic regional OKF priors + asset-class-aware criteria** |
| **Execution Integration** | Requires regex parsing & ad-hoc heuristics | Discrete outputs; no native temporal smoothing | **Vectorized 4P EMA recursive filtering & directional stance logging** |

*Note on Calibration & Benchmark Splits:* The 500-sample NLP calibration benchmark reported in Section 7 was evaluated against hand-curated test bulletins from public financial benchmark collections (Financial PhraseBank and official central bank communiqués). These events are strictly out-of-sample and verified disjoint from training data.

---

## 3. 8-Tier Operational Dataflow & Architecture

```
+-----------------------------------------------------------------------------------------+
|                                8-TIER OPERATIONAL PIPELINE                              |
+-----------------------------------------------------------------------------------------+
[1. Geotargeted & Central Bank RSS Feeds (44 Channels across US, IN, UK, JP)]
       │ (Fed, RBI, Bank of England, Bank of Japan + Regional Publishers)
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
       ├─> event_signals: Math Layer (audit cols: published_at, scored_at, okf_version_hash)
       ├─> event_payloads: Document Layer (Raw JSON, applied OKF rules context)
       └─> pipeline_runs: Ingestion & Scoring Execution Telemetry
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[5. Public Forward Ledger & Signal Engine]      [6. Open Intelligence Terminal (Modular Streamlit)]
- Append-Only forward_test_ledger.csv           - Decomposed src/ui/components/ Architecture
- Multi-Window Recursive EMA (4P, 12P)          - Header Banner & Live Freshness Telemetry
- Hysteresis Deadband Gating (+/- 5.0)          - Plotly Multi-Index Translucent Area Chart
- Directional Stance Logging (Trade Lockout)    - @st.fragment Isolated Live Feed & Ledger
+-----------------------------------------------------------------------------------------+
[7. Dynamic OKF Knowledge Updater (Daily Cron at 00:00 UTC via Google Gemini 3.x)]
- Scrapes macro releases -> Generates reviewable Pull Requests for macro rule shifts
+-----------------------------------------------------------------------------------------+
[8. Operational Health Probe (Every 6 Hours via GitHub Actions & scripts/health_check.py)]
- Probes RSS feeds, Supabase DB pool, and Modal CLM-8B inference endpoint -> Step Summary
+-----------------------------------------------------------------------------------------+
```

### Architectural Breakdown

1. **Geotargeted & Central Bank Ingestion**: Queries 44 RSS channels with exact quoting (`"%22{ticker}%22"`), regional country editions (`&gl=IN`, `&gl=US`, `&gl=GB`, `&gl=JP`), and official central bank feeds (Federal Reserve, RBI, BoE, BoJ).
2. **Regex Affinity Gatekeeper**: Pre-compiles word-boundary regex trees across index tickers (3.0x), constituent companies (2.0x), and central bank anchors (1.0x), rejecting cross-region contaminants.
3. **Dual Deduplication**: Employs intra-run fingerprinting and 48-hour database lookups to prevent redundant inference calls.
4. **Modal Serverless ASGI**: Hosts the Qwen3-8B embedding backbone and CLM projection heads natively on an NVIDIA A10G GPU, bypassing TCP proxy deadlocks and cold-boot delays.
5. **Vertical Partitioning**: Separates numerical vector fields (`id`, `timestamp`, `sentiment_score`, `market_region`, `index_ticker`, `published_at`, `scored_at`, `okf_version_hash`, `model_version`) into `event_signals` and stores raw JSON metadata in `event_payloads`.
6. **Execution & Forward Ledger**: Evaluates recursive multi-span EMAs (4-period, 12-period) and logs out-of-sample forward signals to `reports/forward_test_ledger.csv`. Order execution remains locked out (`ENABLE_TRADE_EXECUTION=false`) for research focus.
7. **Modular Open Intelligence Terminal**: Decomposed into single-responsibility components in `src/ui/components/` and `src/ui/styles.py` with `@st.fragment`-isolated news feeds and public forward evaluation audit views.
8. **Knowledge Governance & Operational Monitoring**: Gemini updates OKF macro rules daily via reviewable Pull Requests (`okf-update-bot`), preventing unauthorized direct commits to `master`, while scheduled health probes monitor system availability every 6 hours.

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
Converts raw relative conviction into a calibrated directional sentiment score:
* `S_dir = sgn(S_rel) × M × 100.0 ∈ [-100.0, +100.0]`

### Stage 5: Time-Series Exponential Moving Average (EMA_α)
A continuous recursive temporal filter smooths raw headline noise for automated order routing:
* `EMA_t = α · Ī_t + (1 - α) · EMA_{t-1}, where α = 2 / (W + 1) = 0.40 (W = 4 hours lookback)`
* *Memory half-life: t_{1/2} = 1.36 periods.*

---

## 5. Open Intelligence Terminal Guide (UI Telemetry)

The dashboard (`src/ui/app.py`) is styled permanently in dark mode (`#020617` canvas, `#0f172a` cards, `#10b981` / `#ef4444` directional accents) and organized into seven distinct modules:

```
+------------------------------------------------------------------------------------+
|                    VALENCE - OPEN INTELLIGENCE TERMINAL LAYOUT                     |
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
|  [SECTION: Public Out-of-Sample Forward Test Ledger & Directional Hit Rate]       |
|  - Quantitative KPI Cards: Directional Hit Rate %, Win Ratio, Cumulative Edge     |
|  - Interactive Historical Signal Audit Table with Timestamp, Region & OKF Commit  |
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

### Autonomous Macro Rules Updater (`src/knowledge_engine/okf_updater.py`)
- Runs daily at `00:00 UTC` via GitHub Actions (`.github/workflows/update_okf.yml`).
- Scrapes central bank speeches and macro releases, prompting Google Gemini to detect regime shifts.
- Implements dynamic model discovery (`client.models.list()`) with automatic fallback (`gemini-3.8-flash` -> `gemini-3.7-flash` -> `gemini-3.5-flash-lite` -> `gemini-3.5-flash`).
- Strict rate pacing (`MIN_REQUEST_INTERVAL = 6.0s`) prevents free-tier API quota exhaustion.
- Submits verified rule updates via reviewable GitHub Pull Requests (`okf-update-bot` branch) with automated document length and diff validation guards (zero direct bot pushes to `master`).

### Autonomous Index Constituents Updater (`scripts/update_constituents.py`)
- Runs fortnightly via GitHub Actions (`.github/workflows/update_constituents.yml`).
- Automatically fetches active index constituents (e.g., S&P 500, Nifty 50, FTSE 100) using free open-source repository APIs.
- Submits updated constituent JSONs via reviewable GitHub Pull Requests (`constituents-update-bot` branch) with structured diff validation checks.

---

## 7. Empirical Benchmarking & LLM Comparison (USP Validation)

To quantitatively evaluate Valence's architectural trade-offs against conventional Generative LLM setups and dictionary methods, the platform includes an automated multi-tier benchmarking suite (`src/benchmark/` & `scripts/run_benchmarks.py`).

### 7.1 Empirical Head-to-Head Comparison

Evaluated on the **Macroeconomic Golden Benchmark Dataset** (`knowledge/benchmark/macro_golden_dataset.json`) across 500 curated central bank policy releases, CPI inflation prints, and trade tariff shocks:

| Quantitative & Operational Dimension | Valence System-One CLM (Sovereign Modal Engine) | Generative LLMs (GPT-4o / Gemini Flash) | Loughran-McDonald Lexicon | Baseline Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Inference Latency (Warm API Call)**| **180–350 ms** (< 500 ms pipeline) | 1,200–2,500 ms (**>4x slower**) | < 0.1 ms (in-memory lookup) | < 500 ms | **PASS** |
| **Container Cold Boot (Serverless)** | **15–30 s** (scale-to-zero GPU boot)| None (managed multi-tenant API) | None (in-process memory) | Scale-to-zero | **PASS** |
| **Bitwise / Float Determinism** | **Deterministic ($\Delta \le 10^{-6}$)** | Stochastic (Decoding temperature drift) | 100% Bitwise Invariant | Reproducible | **PASS** |
| **Expected Calibration Error (ECE)** | **0.0892 (Calibrated Simplex)** | 0.1333 (Overconfident mode collapse) | 0.0549 (Conservative unigram prior) | < 0.10 | **PASS** |
| **Brier Calibration Score** | **0.2034** | 0.2452 | 0.2679 | < 0.25 | **PASS** |
| **Macro F1 Score** | **0.8380** (Nuanced macro semantics) | **0.8545** (Slightly higher recall) | 0.7884 (Rigid lexicon omissions) | > 0.80 | **PASS** |
| **Schema Parse Failure Rate** | **0.00% (Direct Choice Vector)**| 1.8% – 3.2% (JSON syntax drift) | 0.00% | 0.00% | **PASS** |
| **Compute Cost per 10k Events** | **~$0.15 active GPU** (~$0.20 incl. boot & idle) | ~$1.50 – $3.50 (Frontier models; Flash is cheap but has parse drift) | $0.00 (Local CPU) | < $1.00 | **PASS** |
| **Point-in-Time Forward Track Record**| **Active Public Ledger** (`reports/forward_test_ledger.csv`) | N/A | N/A | Target: 90-day horizon / N >= 1,000 signals | **ACTIVE (301 signals since Oct 7, 2026)** |

> **Note on Forward Testing & Alpha Metrics:** Preliminary synthetic backtest figures ($IC = +0.24$, Sharpe $1.70$) reported in earlier drafts have been removed following quantitative review. Those simulations contained synthetic look-ahead artifacts. Directional predictive alpha and calibration are established exclusively via our public, append-only forward-test ledger started on October 7, 2026.
> 
> *Pre-Registration Protocol:* Target evaluation horizon: 90 trading days or $N \ge 1,000$ hourly signals ($N_{\text{eff}} \ge 250$ accounting for serial autocorrelation). Null hypothesis: $H_0: \text{Hit Rate} \le 50.0\%, IC \le 0.0$. Directional hit rate in the ledger measures sentiment continuation across observation intervals ($EMA_{\text{sentiment}} \times \text{Next Raw} > 0$). Multi-region equity asset price return correlation (using daily EOD market data) is evaluated as a decoupled quantitative research tier.

### 7.2 Why Contrastive System-One Outperforms Generative LLMs

1. **Cost-Efficient Batch Inference for Macro Monitoring**: Autoregressive decoding consumes $1,200\text{--}2,500\text{ ms}$ per call and incurs high token fees when ingesting hundreds of regional headlines. Valence processes multi-headline batches in $<350\text{ ms}$ warm latency, enabling cost-effective hourly macroeconomic regime tracking across 40 global news channels without keeping an expensive GPU permanently spinning.
2. **True Probabilistic Simplex Geometry**: Generative LLMs cluster around subjective prompted numbers (`"confidence": 0.80`). Valence projects states directly onto the 2-simplex $\Delta^2$ where $P(\text{Bullish}) + P(\text{Bearish}) + P(\text{Neutral}) = 1.0$, producing mathematically calibrated directional spread $S_{\text{rel}}$.
3. **Endogenous Neutral Damping ($M$)**: Generative LLMs regularly over-trade on routine releases (e.g. jobless claims matching consensus). Valence's neutral attenuation factor $M = |S_{\text{rel}}| \times (1.0 - 0.5 \times P_{\text{neut}})$ suppresses non-directional noise into the $[-5.0, +5.0]$ deadband, filtering low-conviction signals without triggering execution churn.
4. **Reproducible Mathematical State**: Generative LLMs exhibit temperature entropy, creating divergent labels across identical prompt evaluations. Valence guarantees output variance across repeated evaluation runs remains within floating-point epsilon ($\sigma < 10^{-6}$).

---

## 8. Production Operations & Resiliency Matrix

| Service / Layer | Provider | Typical SLA | Failure Mode | Auto-Recovery Mechanism | Operational Caveat |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CLM Inference** | Modal Labs (A10G) | 99.9% | Cold-boot latency / Container timeout | ASGI mount bypasses proxy; graceful fallback to Neutral (0.0) score on timeout. | Free Starter tier ($30/mo) provides ~27 A10G GPU-hours; scale-to-zero keeps per-run time < 2 min. |
| **Relational DB** | Supabase (AWS) | 99.95% | PgBouncer pooler idle connection drop | ThreadedConnectionPool with pre-checkout `_is_alive()` ping; transparent 2-attempt UI retry loop. | Free-tier database pauses after 7 days of inactivity; regular pipeline cron prevents auto-pause. |
| **Knowledge Cron** | Google GenAI | 99.9% | HTTP 429 Quota or HTTP 503 Overload | Paced requests (>= 6.0s interval); immediate failover to secondary Flash models. | Gemini model endpoints retire periodically; fallback registry must track active releases. |
| **Ingestion** | GitHub Actions | 99.9% | Network timeout on regional RSS feed | Async aiohttp timeout guards (10s); continues processing healthy feeds. | Free runner cron executions experience 5–20 minute scheduling jitter during peak hours. |
| **Trade Execution**| Alpaca API | 99.95% | Order reject on outside-hours trading | Paper trading orders automatically queued or logged without blocking pipeline. | Paper trading fills are simulated without market impact or non-US equity support. |

---

## 9. Regulatory Disclaimers & Data Terms

### 9.1 Financial & Research Disclaimer
**Valence is an open-source educational and quantitative macroeconomic research terminal.**
- It does **not** constitute financial, investment, legal, or tax advice.
- It does **not** issue trading recommendations or research analyst reports under the regulations of the **Securities and Exchange Board of India (SEBI)**, the **US Securities and Exchange Commission (SEC)**, the **Financial Conduct Authority (FCA)**, or any other financial regulatory authority.
- All order execution capabilities are strictly confined to **Alpaca Paper Trading** for simulated algorithmic evaluation. Real capital should never be committed solely on the basis of directional sentiment scores or automated signals generated by this platform.

### 9.2 Data Licensing & Redistribution Notice
- The regional news feeds ingested via Google News RSS are accessed for non-commercial academic research, open-source testing, and prototyping demonstrations under standard fair-use parameters.
- For commercial deployments, feeds should be supplemented or substituted with authorized publisher APIs, direct Central Bank RSS bulletins (Federal Reserve, Reserve Bank of India, Bank of England, Bank of Japan), or licensable open data initiatives (e.g. GDELT).

---

*Valence Technical Documentation • Version 2.7.0 • Maintained for Open-Source Quantitative Research*
