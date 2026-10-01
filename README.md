# Global Macro-Sentiment Tracker 📊📈

[![Pipeline Status](https://github.com/Shivam-Jha96/gsp/actions/workflows/deploy.yml/badge.svg)](https://github.com/Shivam-Jha96/gsp/actions/workflows/deploy.yml)
[![OKF Updater](https://github.com/Shivam-Jha96/gsp/actions/workflows/update_okf.yml/badge.svg)](https://github.com/Shivam-Jha96/gsp/actions/workflows/update_okf.yml)
[![Dashboard](https://img.shields.io/badge/Live_Dashboard-Streamlit-FF4B4B?logo=streamlit)](https://macro-sentiment-tracker.streamlit.app/)

An AI-driven macro-sentiment analysis terminal that reads thousands of breaking global financial news events in real-time, scores their market impact using a custom **Contrastive-LM System-One** model on a serverless GPU, and triggers automated paper trading signals — all while dynamically updating its own knowledge base.

---

## 🏗️ Architecture (Phase 1 MVP)

```mermaid
flowchart TD
    subgraph "1. Data Ingestion"
        GN[Global News Feeds] & GR[Reuters Feeds] -->|Poll 20 Indices| Poller[Async RSS Poller]
    end
    
    subgraph "2. AI Engine (CLM-8B on Modal)"
        OKF[(Regional OKF Rules)]
        Poller -->|Headlines| SDK[TypeSafeClient SDK]
        OKF -.->|Macro Context| SDK
        SDK -->|API Call| GPU[Modal A10G GPU]
        GPU --> CLM[System-One Scorer]
    end

    subgraph "3. Database (Supabase)"
        CLM -->|Score Vector| DB1[(event_signals)]
        CLM -->|Raw Text| DB2[(event_payloads)]
    end

    subgraph "4. Signal Engine"
        DB1 -->|Time-Series| EMA[4H EMA Crossover]
        EMA -->|BUY/SELL| Alpaca[Alpaca Paper Trading]
    end

    subgraph "5. Dashboard"
        DB1 & DB2 --> Streamlit[Streamlit App]
    end

    subgraph "6. Knowledge Engine (Daily)"
        NEWS[Macro News RSS] -->|Headlines| GEMINI[Gemini Flash]
        GEMINI -->|Updated Rules| BOT[GitHub Actions Bot]
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
