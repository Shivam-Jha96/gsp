# Global Macro-Sentiment Tracker 📊📈

[![Pipeline Status](https://github.com/Shivam-Jha96/gsp/actions/workflows/deploy.yml/badge.svg)](https://github.com/Shivam-Jha96/gsp/actions/workflows/deploy.yml)
[![OKF Updater](https://github.com/Shivam-Jha96/gsp/actions/workflows/update_okf.yml/badge.svg)](https://github.com/Shivam-Jha96/gsp/actions/workflows/update_okf.yml)
[![Dashboard](https://img.shields.io/badge/Live_Dashboard-Streamlit-FF4B4B?logo=streamlit)](https://macro-sentiment-tracker.streamlit.app/)

An AI-driven macro-sentiment analysis terminal that reads thousands of breaking global financial news events in real-time, scores their market impact using a custom **Contrastive-LM System-One** model on a serverless GPU, and triggers automated paper trading signals — all while dynamically updating its own knowledge base.

---

## 🎯 Unique Selling Proposition (USP): Pure Mathematical Sentiment Engine via Contrastive Language Modeling (CLM)

Conventional financial NLP platforms rely on generative Large Language Models (LLMs) like GPT-4 or Llama to produce qualitative rationales or ad-hoc JSON sentiment scores. In mission-critical quantitative finance, generative LLMs introduce three severe bottlenecks:

1. **Hallucinations & Format Drift**: Autoregressive decoders frequently fail strict schema adherence, corrupt JSON outputs, or hallucinate arbitrary confidence numbers.
2. **Inference Latency Overhead**: Word-by-word autoregressive generation takes 2,000–5,000 ms per headline, creating a major bottleneck for high-throughput market event ingestion.
3. **Confidence Clustering & Mode Collapse**: Prompted LLMs cluster around arbitrary subjective confidence levels (e.g., defaulting to 0.8 or 0.2), failing to capture the true probability mass of market sentiment.

### ⚡ The CLM System-One Solution

The **Global Macro-Sentiment Tracker** eliminates generative token decoding entirely. Instead, our AI Engine uses **Contrastive Language Modeling (CLM-8B)** hosted on a dedicated serverless A10G GPU via Modal. By projecting financial text and macro rules directly into contrastive representation space, the engine evaluates market states using pure mathematical probability vectors:

* **Sub-Second Latency**: Single-pass contrastive scoring runs in **< 250 ms** (>10x faster than generative LLMs).
* **Zero Hallucination Risk**: No text generation or token sampling; outputs are pure deterministic probability distributions.
* **Calibrated Probability Simplex**: Directly computes native probabilities over orthogonal market states where $P(\text{Bullish}) + P(\text{Bearish}) + P(\text{Neutral}) = 1.0$.

| Dimension | Generative LLMs (Autoregressive) | GSP CLM System-One Engine |
| :--- | :--- | :--- |
| **Scoring Mechanism** | Generates text tokens / Prompted JSON | Contrastive representation probability simplex |
| **Inference Latency** | 2,000 – 5,000 ms / headline | **< 250 ms** / headline |
| **Output Stability** | Prone to formatting errors and hallucinations | **100% deterministic mathematical vectors** |
| **Confidence Calibration** | Qualitative clustering (e.g. 0.8 vs 0.2) | **Calibrated relative directional spread** |
| **Signal Noise Handling** | Neutral sentiment easily misclassified | **Explicit neutral attenuation factor** |

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
| **Ingestion** | `aiohttp`, Google News RSS | Async poller fetching ~120 headlines per run across 20 indices in 4 regions (US, IN, UK, JP) |
| **AI Engine** | `Contrastive-LM/CLM-v0.1-8B`, Modal A10G, TypeSafe SDK | System-One mathematical scorer — no token generation, pure probability vectors (-1.0 to +1.0) |
| **Knowledge** | Gemini Flash, Google News RSS | Daily auto-updating OKF rules via Gemini with resilient model fallback chain |
| **Database** | Supabase PostgreSQL | Vertical partitioning: `event_signals` (math layer) + `event_payloads` (document layer) |
| **Signal Engine** | Pandas, Alpaca API | 4-hour EMA crossover strategy routing BUY/SELL orders to paper trading |
| **Dashboard** | Streamlit, Plotly | Dark-mode glassmorphism terminal with auto-scaling charts and live intelligence feed |

---

## 📂 Repository Structure

```text
gsp/
├── .github/workflows/
│   ├── deploy.yml              # Sentiment pipeline (every 2 hours)
│   └── update_okf.yml          # Dynamic OKF updater (daily)
├── docs/                       # Quantitative & architectural documentation
│   ├── architecture_and_workflow.md  # End-to-end architecture & workflows
│   ├── sentiment_math.md             # CLM quantitative math & scoring proofs
│   └── build_progress.md             # Milestone build progress log
├── knowledge/                  # Auto-updated regional trading rules
│   ├── us_macro.okf.md
│   ├── india_macro.okf.md
│   ├── uk_macro.okf.md
│   └── japan_macro.okf.md
├── src/
│   ├── ai_engine/              # Modal serverless GPU (CLM System-One)
│   ├── database/               # Supabase connection pooler & SQL schemas
│   ├── ingestion/              # Async RSS feed poller
│   ├── knowledge_engine/       # Gemini-powered OKF updater
│   ├── signal_engine/          # Pandas EMA calculator & Alpaca routing
│   ├── ui/                     # Streamlit dashboard
│   └── main.py                 # Unified pipeline entry point
└── requirements.txt
```

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
| **Sentiment Pipeline** (`deploy.yml`) | Every 2 hours | Ingestion → AI Scoring → Database → Paper Trading |
| **OKF Knowledge Updater** (`update_okf.yml`) | Daily at 00:00 UTC | Gemini analyzes macro policy news and auto-commits updated OKF trading rules |

Both workflows can also be triggered manually via `workflow_dispatch` from the GitHub Actions UI.

---

## 📊 Live Dashboard

The live dashboard is deployed on Streamlit Community Cloud:

**🔗 [macro-sentiment-tracker.streamlit.app](https://macro-sentiment-tracker.streamlit.app/)**
