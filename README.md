# Valence 📊📈
### Open-Source Quantitative Macroeconomic Sentiment & Directional Signal Engine

[![CI Pipeline](https://github.com/Shivam-Jha96/gsp/actions/workflows/ci.yml/badge.svg)](https://github.com/Shivam-Jha96/gsp/actions/workflows/ci.yml)
[![Pipeline Status](https://github.com/Shivam-Jha96/gsp/actions/workflows/deploy.yml/badge.svg)](https://github.com/Shivam-Jha96/gsp/actions/workflows/deploy.yml)
[![Operational Health](https://github.com/Shivam-Jha96/gsp/actions/workflows/health_check.yml/badge.svg)](https://github.com/Shivam-Jha96/gsp/actions/workflows/health_check.yml)
[![OKF Updater](https://github.com/Shivam-Jha96/gsp/actions/workflows/update_okf.yml/badge.svg)](https://github.com/Shivam-Jha96/gsp/actions/workflows/update_okf.yml)
[![Dashboard](https://img.shields.io/badge/Live_Dashboard-Streamlit-FF4B4B?logo=streamlit)](https://valence.streamlit.app/)

<p align="center">
  <img src="assets/valence_social_preview.png" alt="Valence Social Preview Banner" width="100%" style="border-radius: 12px; border: 1px solid #1e293b;" />
</p>

**Valence** (formerly Global Sentiment Platform of Share Markets / GSP) is an open-source quantitative macroeconomic sentiment and directional signal engine. It reads global financial and geopolitical news events across four major equity hubs (US, India, UK, Japan), scores their directional impact using a **Contrastive-LM System-One (CLM-8B)** model on serverless GPU infrastructure, and triggers automated paper trading signals — all while dynamically updating its regional macroeconomic knowledge base.

---

## 🎯 Unique Selling Proposition (USP): Pure Mathematical Sentiment Engine via Contrastive Language Modeling (CLM)

Conventional financial NLP platforms rely on generative Large Language Models (LLMs) like GPT-4 or Llama to produce qualitative rationales or ad-hoc JSON sentiment scores. In quantitative finance, generative LLMs introduce three severe bottlenecks:

1. **Hallucinations & Format Drift**: Autoregressive decoders frequently fail strict schema adherence, corrupt JSON outputs, or hallucinate arbitrary confidence numbers.
2. **Inference Latency Overhead**: Word-by-word autoregressive generation takes 1,200–2,500 ms per headline, creating a major cost and throughput bottleneck for continuous news event ingestion.
3. **Confidence Clustering & Mode Collapse**: Prompted LLMs cluster around arbitrary subjective confidence levels (e.g., defaulting to 0.8 or 0.2), failing to capture the true probability mass of market sentiment.

### ⚡ The CLM System-One Solution

**Valence** eliminates generative token decoding entirely. Instead, our AI Engine utilizes the contrastive inference paradigm of **TypeSafe AI's Jev** System-One model (via the official SDK), deployed on serverless GPU infrastructure via Modal. By evaluating financial text and macro rules directly in contrastive representation space and applying rigorous financial mathematics, the engine evaluates market states using pure mathematical probability vectors:

* **Low-Latency Batch Inference**: Single-pass contrastive scoring runs in **180–350 ms warm API latency** (>4x faster than generative LLMs), enabling cost-efficient hourly macro monitoring without GPU keep-alive expenses.
* **Zero Hallucination Risk**: No text generation or token sampling; outputs are pure deterministic probability distributions.
* **Calibrated Probability Simplex**: Directly computes native probabilities over orthogonal market states where $P(\text{Bullish}) + P(\text{Bearish}) + P(\text{Neutral}) = 1.0$.

| Dimension | Generative LLMs (Autoregressive) | TypeSafe AI (Vanilla Jev) | Valence CLM System-One Engine |
| :--- | :--- | :--- | :--- |
| **Scoring Mechanism** | Generates text tokens / Prompted JSON | Contrastive representation / Choice probabilities | **Bipolar Simplex Projection + Quantitative Spread ($S_{\text{rel}}$)** |
| **Inference Latency** | 1,200 – 2,500 ms / headline | 70 – 500 ms / call (standard hosted API) | **180–350 ms warm API / batch** (serverless A10G) |
| **Output Stability** | Prone to formatting errors and hallucinations | Deterministic choice probabilities ($P_i \in [0, 1]$) | **Deterministic continuous momentum ($-100$ to $+100$)** |
| **Confidence Calibration** | Qualitative clustering (e.g. 0.8 vs 0.2) | Raw probabilities; uncalibrated directional spread | **Calibrated relative directional conviction ($S_{\text{rel}}$)** |
| **Signal Noise Handling** | Neutral sentiment easily misclassified | Prone to neutral flatlining ($P \ge 0.90$) on dense context | **Explicit non-linear neutral attenuation factor ($M$)** |
| **Macro & Asset Conditioning** | Unstructured prompts; prone to attention drift | Static criteria; no dynamic macro regime awareness | **Dynamic regional OKF priors + asset-class-aware criteria** |
| **Execution Integration** | Requires regex parsing & ad-hoc heuristics | Discrete outputs; no native temporal smoothing | **Vectorized 4P EMA recursive filtering & Alpaca paper trading** |

---

### 📐 Mathematical Scoring Engine

Our quantitative sentiment pipeline transforms unstructured global headlines into high-precision trading signals across five mathematical stages:

```
[Regional Headline + OKF Macro Context]
                   │
                   ▼
  1. Contrastive Representation Scoring
     Extraction: P(Bullish), P(Bearish), P(Neutral)
                   │
                   ▼
  2. Relative Directional Spread Calculation
     S_rel = (P(Bullish) - P(Bearish)) / (P(Bullish) + P(Bearish))
                   │
                   ▼
  3. Conviction Magnitude with Neutral Attenuation
     Magnitude = |S_rel| * (1.0 - 0.5 * P(Neutral))
                   │
                   ▼
  4. Signed Directional Calibration
     Score = sign(S_rel) * Magnitude ∈ [-1.0, +1.0]
                   │
                   ▼
  5. Terminal Sentiment Index Scaling
     Index = Score * 100 ∈ [-100, +100]
```

#### 1. Ingestion with Open Knowledge Formulation (OKF)
Each ingested headline is paired with dynamic regional macroeconomic rules (`knowledge/*_macro.okf.md`) containing central bank policies, interest rate regimes, and inflation sensitivities:
$$\text{State} = \mathcal{T}(\text{Headline}, \text{Summary}) \oplus \text{OKF}_{\text{Region}}$$

#### 2. Native Probability Distribution Extraction
Rather than generating text, the CLM System-One engine evaluates the state against canonical hypotheses, outputting an exact probability distribution:
$$P(\text{Bullish}), \quad P(\text{Bearish}), \quad P(\text{Neutral}) \quad \text{where} \quad \sum_{c \in C} P(c) = 1.0$$

#### 3. Relative Directional Spread ($S_{\text{rel}}$)
To isolate directional market conviction from neutral mass, the engine calculates the normalized spread across active directional poles:
$$S_{\text{rel}} = \frac{P(\text{Bullish}) - P(\text{Bearish})}{P(\text{Bullish}) + P(\text{Bearish})}$$
*(When directional mass $P(\text{Bullish}) + P(\text{Bearish}) \le 10^{-5}$, $S_{\text{rel}}$ is set to $0.0$ to avoid numerical instability).*

#### 4. Conviction Magnitude Weighted by Neutral Attenuation
High neutral mass ($P(\text{Neutral}) \to 1.0$) indicates ambiguous or conflicting macro events. The conviction magnitude is attenuated accordingly:
$$\text{Magnitude} = |S_{\text{rel}}| \times \left(1.0 - 0.5 \times P(\text{Neutral})\right)$$

#### 5. Signed Directional Score & Terminal Sentiment Index
- **Signed Directional Score ($S \in [-1.0, +1.0]$)**:
  $$S = \begin{cases} 
  0.0 & \text{if Choice} = \text{Neutral} \\
  +|S_{\text{rel}}| \times (1.0 - 0.5 \times P(\text{Neutral})) & \text{if Choice} = \text{Bullish} \\
  -|S_{\text{rel}}| \times (1.0 - 0.5 \times P(\text{Neutral})) & \text{if Choice} = \text{Bearish}
  \end{cases}$$
- **Terminal Sentiment Index ($I \in [-100, +100]$)**:
  $$I = S \times 100$$
  The resulting continuous index provides a high-resolution signal for real-time visualization and our 4-hour Exponential Moving Average (EMA) crossover trading strategy.

---

### 📚 Comprehensive Documentation

For deep technical derivations and complete architectural workflows, refer to the dedicated documentation:

* 📖 [**Sentiment Math & Scoring Engine Proofs**](docs/sentiment_math.md) — Complete mathematical derivations, edge-case analysis, worked numerical examples, and comparison matrices.
* 🏛️ [**Architecture & System Workflow**](docs/architecture_and_workflow.md) — Comprehensive layer-by-layer specifications, dataflow lifecycle, database partitioning schemas, and production deployment topology.

---

## 🏗️ Architecture (Phase 1 MVP)

```mermaid
flowchart TD
    subgraph S1 ["1. Data Ingestion"]
        GN["Global News Feeds"]
        GR["Reuters Feeds"]
        Poller["Async RSS Poller"]
        GN -->|Poll Feeds| Poller
        GR -->|Poll Feeds| Poller
    end
    
    subgraph S2 ["2. AI Engine (CLM-8B on Modal)"]
        OKF[("Regional OKF Rules")]
        SDK["TypeSafeClient SDK"]
        GPU["Modal A10G GPU"]
        CLM["System-One Scorer"]
        Poller -->|Headlines| SDK
        OKF -.->|Macro Context| SDK
        SDK -->|API Call| GPU
        GPU --> CLM
    end

    subgraph S3 ["3. Database (Supabase)"]
        DB1[("event_signals")]
        DB2[("event_payloads")]
        CLM -->|Score Vector| DB1
        CLM -->|Raw Text| DB2
    end

    subgraph S4 ["4. Signal Engine"]
        EMA["4H EMA Crossover"]
        Alpaca["Alpaca Paper Trading"]
        DB1 -->|Time-Series| EMA
        EMA -->|BUY or SELL| Alpaca
    end

    subgraph S5 ["5. Dashboard"]
        Streamlit["Streamlit App"]
        DB1 --> Streamlit
        DB2 --> Streamlit
    end

    subgraph S6 ["6. Knowledge Engine (Daily)"]
        NEWS["Macro News RSS"]
        GEMINI["Gemini Flash"]
        BOT["GitHub Actions Bot"]
        NEWS -->|Headlines| GEMINI
        GEMINI -->|Updated Rules| BOT
        BOT -->|Auto-Commit| OKF
    end
```

### Core Components

| Layer | Tech | Description |
|-------|------|-------------|
| **Ingestion** | `aiohttp`, Google News RSS, Classifier, Constituent OKF, Deduplicator | Async poller with declarative market registry, index constituent entity mapping, affinity classifier, and multi-stage deduplication |
| **AI Engine** | `Contrastive-LM/CLM-v0.1-8B`, Modal A10G, TypeSafe SDK | Grounded System-One mathematical scorer — focused state conditioning, explicit market criteria anchors, continuous probability vectors (-1.0 to +1.0) |
| **Knowledge** | Gemini Flash, Google News RSS, Declarative Constituents | Daily auto-updating OKF macro rules via Gemini and curated regional index constituent registries |
| **Database** | Supabase PostgreSQL | Vertical partitioning: `event_signals` (math layer) + `event_payloads` (document layer) |
| **Signal Engine** | Pandas, Alpaca API | 4-hour EMA crossover strategy routing BUY/SELL orders to paper trading |
| **Dashboard** | Streamlit, Plotly | Dark-mode glassmorphism terminal with dynamic regional filtering, deduplication, auto-scaling charts and live feed |

---

## 📂 Repository Structure

```text
gsp/
├── .github/workflows/
│   ├── ci.yml                  # CI Pipeline PyTest runner & compileall
│   ├── deploy.yml              # Sentiment pipeline (every 2 hours)
│   ├── health_check.yml        # Operational subsystem health probe (every 6 hours)
│   ├── update_okf.yml          # Dynamic OKF updater & PR creator (daily)
│   ├── update_constituents.yml # Index constituents updater (fortnightly)
│   ├── db_cleanup.yml          # Database retention purge workflow
│   └── reclassify_db.yml       # Database integrity, deduplication & re-scoring workflow
├── docs/                       # Quantitative & architectural documentation
│   ├── architecture_and_workflow.md  # 8-tier architecture & workflow specifications
│   ├── sentiment_math.md             # CLM quantitative math & scoring proofs
│   ├── wiki_home.md                  # Comprehensive technical wiki
│   └── build_progress.md             # Multi-phase milestone build progress log
├── knowledge/                  # Auto-updated regional trading rules & constituents
│   ├── benchmark/              # Curated Macroeconomic Golden Benchmark Dataset
│   ├── us_macro.okf.md
│   ├── us_constituents.okf.json
│   ├── india_macro.okf.md
│   ├── india_constituents.okf.json
│   ├── uk_macro.okf.md
│   ├── uk_constituents.okf.json
│   ├── japan_macro.okf.md
│   └── japan_constituents.okf.json
├── reports/                    # Generated institutional benchmark & forward test reports
│   ├── forward_test_ledger.csv # Append-only public forward-testing evaluation ledger
│   ├── benchmark_report.md     # 4-tier benchmark evaluation report
│   └── benchmark_data.json     # Benchmark metrics data
├── scripts/
│   ├── run_benchmarks.py       # Unified 4-tier quantitative benchmark CLI runner
│   ├── health_check.py         # Subsystem operational health probe diagnostics CLI
│   ├── db_cleanup.py           # Database purge & retention maintenance
│   ├── reclassify_database.py  # Historical contaminant scan & purge utility
│   ├── update_constituents.py  # Fortnightly constituent synchronizer
│   ├── add_audit_columns.sql   # Database audit schema migration script
│   └── migrate_to_partitions.sql # Table partitioning migration script
├── src/
│   ├── ai_engine/              # Modal serverless GPU (CLM System-One)
│   ├── benchmark/              # 4-tier benchmarking engine & econometric metrics
│   │   ├── backtest_engine.py  # Causal walk-forward backtester vs Buy & Hold
│   │   ├── classifier_evaluator.py # Regional affinity & noise filtering benchmark
│   │   ├── nlp_evaluator.py    # Model calibration (ECE, Brier) vs FinBERT & LM
│   │   ├── predictive_metrics.py   # Information Coefficient, Hit Rate, Sharpe/Sortino
│   │   └── system_profiler.py  # Database pool & UI fragment latency profiler
│   ├── config/                 # Declarative market registry & constituent loaders
│   │   ├── asset_classes.json  # Global asset-class dynamic criteria (equity, fixed_income, etc.)
│   │   ├── market_registry.json# Regional market, index, and central bank configurations
│   │   └── market_registry.py  # Dynamic RSS feed generator & registry accessors
│   ├── database/               # Supabase connection pooler, SQL schemas & pipeline telemetry
│   │   ├── client.py           # ThreadedConnectionPool manager with pre-checkout ping
│   │   ├── schemas.sql         # Vertical partitioning schema & audit columns
│   │   └── telemetry.py        # Context-managed pipeline run telemetry & freshness
│   ├── ingestion/              # Async RSS poller, regional affinity classifier & deduplicator
│   │   ├── api_clients.py      # Lightweight XML RSS parser
│   │   ├── classifier.py       # Regex entity trie affinity classifier
│   │   ├── dedup.py            # SHA-256 canonical fingerprint deduplicator
│   │   └── poller.py           # Async aiohttp multi-feed poller
│   ├── knowledge_engine/       # Dynamic Gemini-powered OKF updater
│   │   └── okf_updater.py      # Resilient multi-model fallback chain & PR creator
│   ├── signal_engine/          # Signal generation, forward testing & execution
│   │   ├── ema.py              # Vectorized recursive multi-window EMA calculator
│   │   ├── forward_tester.py   # Out-of-sample forward evaluation & in-memory metrics
│   │   └── cron_jobs.py        # Directional crossover strategy & paper trading
│   ├── ui/                     # Modular Streamlit dashboard & styling engine
│   │   ├── components/         # Single-responsibility components (header, toolbar, analytics, feed, ledger)
│   │   ├── styles.py           # Master permanent dark theme CSS & typography engine
│   │   ├── state_persistence.py# Dual-layer query-param & local storage persistence
│   │   └── app.py              # Lightweight dashboard entry-point orchestrator
│   └── main.py                 # Unified pipeline entry point
├── tests/
│   └── unit/                   # Automated unit test suite (66 tests passing)
│       ├── test_backtest_causality.py
│       ├── test_benchmark_metrics.py
│       ├── test_classifier_and_registry.py
│       ├── test_dedup_and_sentiment.py
│       ├── test_forward_tester.py
│       ├── test_okf_updater.py
│       ├── test_signal_engine.py
│       ├── test_state_persistence.py
│       ├── test_telemetry.py
│       ├── test_ui_chart_config.py
│       ├── test_ui_fragment_isolation.py
│       └── test_valence_branding.py
└── requirements.txt
```

---

## 🧪 Quantitative Benchmarking & Alpha Validation

Valence includes a native, automated **4-Tier Quantitative Benchmarking Suite** verifying model calibration, regional filtering isolation, predictive alpha, and infrastructure latency:

```bash
# Run all 4 benchmark tiers and export markdown/JSON reports
python scripts/run_benchmarks.py --all

# Run specific evaluation tiers
python scripts/run_benchmarks.py --tier nlp         # AI Calibration (Acc, F1, ECE, Brier, Latency)
python scripts/run_benchmarks.py --tier classifier  # Contamination & Noise Rejection %
python scripts/run_benchmarks.py --tier alpha       # Historical Backtest on SPY (Sharpe, MDD, IC)
python scripts/run_benchmarks.py --tier system      # Supabase DB & UI Fragment Latency

# Run automated unit test suite (66 tests)
python -m unittest discover tests/unit -v

# Run subsystem operational health probe
python scripts/health_check.py
```

Automated reports are generated at `reports/benchmark_report.md` and `reports/benchmark_data.json`. Out-of-sample forward signals are logged point-in-time to `reports/forward_test_ledger.csv`.

### 🏆 Empirical Benchmark Results: Valence System-One CLM vs. Generative LLMs vs. Baselines

Evaluated on the **Macroeconomic Golden Benchmark Dataset** (500 curated macroeconomic releases across US, IN, UK, and JP central bank policy, inflation, and trade events):

| Performance & Operational Dimension | Valence System-One CLM Engine | Generative LLMs (GPT-4o / Gemini Flash) | Loughran-McDonald Lexicon | Baseline Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Inference Latency (Warm API Call)**| **180–350 ms** (< 500 ms pipeline) | 1,200–2,500 ms (**>4x slower**) | < 0.1 ms (in-memory lookup) | < 500 ms | **PASS** |
| **Container Cold Boot (Serverless)** | **15–30 s** (scale-to-zero GPU boot)| None (managed multi-tenant API) | None (in-process memory) | Scale-to-zero | **PASS** |
| **Bitwise / Float Determinism** | **Deterministic ($\Delta \le 10^{-6}$)** | Stochastic (Decoding temperature drift) | 100% Bitwise Invariant | Reproducible | **PASS** |
| **Expected Calibration Error (ECE)** | **0.0892 (Calibrated Simplex)** | 0.1333 (Overconfident clustering) | 0.0549 (Conservative unigram prior) | < 0.10 | **PASS** |
| **Brier Calibration Score** | **0.2034** | 0.2452 | 0.2679 | < 0.25 | **PASS** |
| **Macro F1 Score** | **0.8380** (Nuanced macro semantics) | **0.8545** (Slightly higher recall) | 0.7884 (Rigid lexicon omissions) | > 0.80 | **PASS** |
| **Schema Parse Failure Rate** | **0.00% (Native Choice Vector)** | 1.8% – 3.2% (JSON syntax drift) | 0.00% | 0.00% | **PASS** |
| **Compute Cost per 10k Events** | **~$0.15 active GPU** (~$0.20 incl. boot & idle) | ~$1.50 – $3.50 (Frontier models; Flash is cheap but has parse drift) | $0.00 (Local CPU) | < $1.00 | **PASS** |
| **Point-in-Time Forward Track Record**| **Active Public Ledger** (`reports/forward_test_ledger.csv`) | N/A | N/A | Target: 90-day horizon / N >= 1,000 signals | **ACTIVE (301 signals since Oct 7, 2026)** |

> **Note on Forward Testing & Alpha Metrics:** Preliminary synthetic backtest figures ($IC = +0.24$, Sharpe $1.70$) reported in earlier drafts have been removed following quantitative review. Those simulations contained synthetic look-ahead artifacts. Directional predictive alpha and calibration are established exclusively via our public, append-only forward-test ledger started on October 7, 2026.
> 
> *Pre-Registration Protocol:* Target evaluation horizon: 90 trading days or $N \ge 1,000$ hourly signals ($N_{\text{eff}} \ge 250$ accounting for serial autocorrelation). Null hypothesis: $H_0: \text{Hit Rate} \le 50.0\%, IC \le 0.0$. Directional hit rate in the ledger measures sentiment continuation across observation intervals ($EMA_{\text{sentiment}} \times \text{Next Raw} > 0$). Multi-region equity asset price return correlation (using daily EOD market data) is evaluated as a decoupled quantitative research tier.

---


## 🚀 Getting Started

### 1. Prerequisites
You will need API keys from the following providers:
- **Alpaca** — Paper Trading execution
- **Supabase** — PostgreSQL Database (`DATABASE_URL`)
- **TypeSafe** — CLM System-One AI inference (`TYPESAFE_API_KEY`)
- **Gemini** — Dynamic OKF knowledge updates (`GEMINI_API_KEY`)

### 2. Database Setup
Apply the database schemas to your Supabase instance by executing the SQL commands in `src/database/schemas.sql` via the Supabase SQL Editor.

### 3. Local Installation
```bash
git clone https://github.com/Shivam-Jha96/gsp.git
cd gsp
pip install -r requirements.txt
```

### 4. Environment Variables
```bash
export ALPACA_API_KEY="your_api_key"
export ALPACA_SECRET_KEY="your_secret_key"
export DATABASE_URL="postgresql://postgres.[PROJECT]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
export TYPESAFE_API_KEY="your_typesafe_api_key"
export GEMINI_API_KEY="your_gemini_api_key"
```

### 5. Running the Pipeline
```bash
PYTHONPATH=src python src/main.py
```

---

## ⚙️ Automated CI/CD

| Workflow | Schedule | Description |
|----------|----------|-------------|
| **CI Pipeline** (`ci.yml`) | On Push & Pull Request | Automated syntax compilation and 66-test unit test suite execution |
| **Sentiment Pipeline** (`deploy.yml`) | Every 2 hours | Ingestion → AI Scoring → Database → Forward Ledger |
| **Operational Health Probe** (`health_check.yml`) | Every 6 hours | Probes regional RSS feeds, Supabase DB pool, and Modal CLM endpoint |
| **OKF Knowledge Updater** (`update_okf.yml`) | Daily at 00:00 UTC | Gemini analyzes macro policy news and opens reviewable PRs for rule shifts |
| **Index Constituents Updater** (`update_constituents.yml`) | Fortnightly | Automated update of regional index constituents using open-source financial APIs |
| **Database Retention Purge** (`db_cleanup.yml`) | Daily at 03:00 UTC | Enforces rolling data retention window and cleans orphaned records |
| **Reclassification & Purge** (`reclassify_db.yml`) | Manual (`workflow_dispatch`) | Scans historical Supabase records and audits/purges regional contaminants |

All workflows can also be triggered manually via `workflow_dispatch` from the GitHub Actions UI.

---

## 📊 Live Dashboard

The live dashboard is deployed on Streamlit Community Cloud:

**🔗 [valence.streamlit.app](https://valence.streamlit.app/)**

---

## ⚖️ Regulatory Disclaimers & Data Terms

### Financial & Research Disclaimer
**Valence is an open-source educational and quantitative macroeconomic research terminal.**
- It does **not** constitute financial, investment, legal, or tax advice.
- It does **not** issue trading recommendations or research analyst reports under the regulations of the **Securities and Exchange Board of India (SEBI)**, the **US Securities and Exchange Commission (SEC)**, the **Financial Conduct Authority (FCA)**, or any other financial regulatory authority.
- All order execution capabilities are strictly confined to **Alpaca Paper Trading** for simulated algorithmic evaluation. Real capital should never be committed solely on the basis of directional sentiment scores or automated signals generated by this platform.

### Data Licensing & Redistribution Notice
- Regional news feeds ingested via Google News RSS are accessed for non-commercial academic research, open-source testing, and prototyping demonstrations under standard fair-use parameters.
- For commercial deployments, feeds should be supplemented or substituted with authorized publisher APIs, direct Central Bank RSS bulletins (Federal Reserve, Reserve Bank of India, Bank of England, Bank of Japan), or licensable open data initiatives (e.g. GDELT).
