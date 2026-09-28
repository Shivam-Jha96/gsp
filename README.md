# Global Macro-Sentiment Tracker 🌍📈

An ultra-low-latency, AI-driven stock prediction pipeline that evaluates global financial news in real-time, filters noise, and triggers automated trading signals. The system explicitly tracks the Top 5 Global Indices (e.g., S&P 500, Nifty 50, FTSE 100) to predict major market trends with a high signal-to-noise ratio.

---

## 🏗️ Architecture (Phase 1 MVP)

This repository currently implements the **Phase 1 MVP**, utilizing a lightweight, cost-effective tech stack focused on algorithmic validation.

1. **Ingestion Layer:** Asynchronous Python poller (`aiohttp`) that fetches financial news from global RSS feeds (US, IN, UK, JP).
2. **Knowledge Layer:** Strict decoupling of static, region-specific trading rules using Google OKF (Open Knowledge Format) via GitOps (`knowledge/`).
3. **AI Engine:** Deterministic System-One scoring utilizing a ZeroGPU CLM-8B model (`@spaces.GPU`) hosted on Hugging Face Spaces.
4. **Database (Agile PostgreSQL):** Supabase database utilizing strict **Vertical Partitioning** (`event_signals` for math, `event_payloads` for text) and advanced indexing (BRIN, Composite B-Tree).
5. **Signal & Execution Engine:** A cron-triggered Pandas script that calculates a 4-hour Exponential Moving Average (EMA) and routes directional signals to **Alpaca** for Paper Trading.

*For full details on the Phase 2 (V2) Enterprise Scaling plan (Java, Spring Boot, AWS Bedrock), see [`docs/architecture.md`](docs/architecture.md).*

---

## 📂 Repository Structure

```text
gsp/
├── .github/workflows/       # GitHub Actions (Automated Cron Pipeline)
├── docs/                    # Architecture diagrams, PRDs, and Build Progress
├── knowledge/               # Static regional trading rules (us_macro.okf.md, etc.)
├── src/                     # Core Micro-Components
│   ├── ai_engine/           # ZeroGPU inference logic
│   ├── database/            # Supabase connection pooler & SQL schemas
│   ├── ingestion/           # Async RSS feed poller
│   ├── signal_engine/       # Pandas EMA calculator & Alpaca routing
│   └── main.py              # Unified pipeline entry point
└── requirements.txt         # Python dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites
You will need API keys and connection strings from the following providers:
*   **Alpaca:** For Paper Trading execution.
*   **Supabase:** For the PostgreSQL Database (`DATABASE_URL`).
*   **Hugging Face:** For the AI Inference (`HF_TOKEN`).

### 2. Database Setup
Before running the pipeline, you must apply the database schemas to your Supabase instance:
Execute the SQL commands found in `src/database/schemas.sql` in your Supabase SQL Editor.

### 3. Local Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/Shivam-Jha96/gsp.git
cd gsp
pip install -r requirements.txt
```

### 4. Environment Variables
Set the following environment variables in your terminal (or `.env` file) for local testing:
```bash
export ALPACA_API_KEY="your_api_key"
export ALPACA_SECRET_KEY="your_secret_key"
export DATABASE_URL="postgresql://postgres.[YOUR_PROJECT]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
export HF_TOKEN="your_huggingface_token"
```

### 5. Running the Pipeline
To execute a dry-run of the end-to-end pipeline (Ingestion -> Scoring -> Database -> Trading):
```bash
python src/main.py
```

---

## 🤖 Automated CI/CD Execution
This repository is configured with a GitHub Actions workflow (`deploy.yml`). 
Once you add the above environment variables to your **GitHub Repository Secrets**, the action will automatically run the pipeline on a 4-hour cron schedule.
