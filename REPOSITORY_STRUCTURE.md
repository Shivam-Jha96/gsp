# Recommended Repository Structure: Global Macro-Sentiment Tracker

Based on the Product Requirements Document (PRD) and High-Level Design (HLD) provided, here is a robust, modular, and scalable repository structure that adheres to industry standards.

## Directory Layout

```text
gsp/
├── .github/                       # CI/CD and DevOps
│   └── workflows/
│       ├── ci.yml                 # Automated testing (PyTest) via GitHub Actions
│       └── deploy.yml             # Deployment to Render/Railway/Spaces
├── docs/                          # Documentation
│   ├── Global_Stock_Predictor_PRD.pdf # The original PRD
│   └── architecture.md            # System architecture details and diagrams
├── knowledge/                     # Knowledge Management Layer (GitOps controlled)
│   ├── us_macro.okf.md            # US region OKF rules
│   ├── india_macro.okf.md         # India region OKF rules
│   └── uk_macro.okf.md            # UK region OKF rules (and others: JP)
├── src/                           # Main Source Code (Monorepo approach for microservices)
│   ├── ingestion/                 # Global Ingestion Worker
│   │   ├── __init__.py
│   │   ├── api_clients.py         # Clients for Yahoo Finance, RSS feeds
│   │   └── poller.py              # Reliable async polling logic
│   ├── ai_engine/                 # Regional AI Engine (HuggingFace Spaces)
│   │   ├── __init__.py
│   │   ├── inference.py           # ZeroGPU CLM-8B integrations
│   │   └── context_injector.py    # Logic to map and inject regional .okf.md files
│   ├── signal_engine/             # Signal Generation (Vector math via Pandas)
│   │   ├── __init__.py
│   │   ├── ema.py                 # 4-hour Exponential Moving Average logic
│   │   └── cron_jobs.py           # Schedulers and triggers
│   ├── database/                  # Agile PostgreSQL (Supabase) Layer
│   │   ├── __init__.py
│   │   ├── client.py              # Connection pooling & PgBouncer integration
│   │   └── schemas.sql            # Vertical partitioning & BRIN/Composite indexing definitions
│   ├── ui/                        # Presentation Layer
│   │   ├── app.py                 # Streamlit main dashboard entry point
│   │   └── components/            # Reusable UI widgets
│   └── core/                      # Shared business logic and utilities
│       ├── __init__.py
│       ├── config.py              # Centralized environment variable management
│       └── logger.py              # Standardized logging
├── tests/                         # Testing & Benchmarking Approach
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration testing (e.g., proper OKF routing)
│   └── backtest/                  # Benchmarking win rate (>55%) vs historical data
├── docker/                        # Containerization Definitions
│   ├── ingestion.Dockerfile       # Dockerfile for Render/Railway deployment
│   └── ui.Dockerfile              # Streamlit containerization
├── .gitignore                     # Standard Python and environment ignores
├── requirements.txt               # Dependencies (Pandas, Streamlit, Supabase, etc.)
└── README.md                      # Project overview, setup, and run instructions
```

## Architectural Justifications

1. **Separation of Concerns (Modularity):**
   - The `src/` directory is logically partitioned into functional micro-components: `ingestion`, `ai_engine`, `signal_engine`, `database`, and `ui`.
   - This directly maps to the PRD's container architecture, allowing different teams or developers to work on individual components (e.g., prompt engineering in `ai_engine` vs vector math in `signal_engine`) with minimal merge conflicts.

2. **Knowledge Management Layer (`knowledge/`):**
   - Extracts the Google OKF (Open Knowledge Format) files from the core codebase.
   - Enables the requested **GitOps for Knowledge** practice. Traders and analysts can submit PRs to `.okf.md` files without touching Python code, ensuring clean human oversight.

3. **Scalability & Deployment (`docker/` & `.github/`):**
   - Standardized Dockerfiles allow components like the Ingestion Worker to be deployed flexibly to container hosts like Render or Railway.
   - GitHub Actions workflows are primed for CI (PyTest) and CD (Docker builds), ensuring safe integrations.

4. **Database & Infrastructure as Code (`src/database/`):**
   - Consolidating schemas and index setups ensures the Vertical Partitioning strategy and specialized indexing (BRIN, Composite) are version-controlled and reproducible across environments.

5. **Testing & Benchmarking (`tests/`):**
   - Distinct test directories for `unit`, `integration`, and `backtest` align perfectly with the PRD's QA and Benchmarking strategy. The integration folder will specifically test the dynamic routing of regional OKF files, and `backtest` will provide a dedicated space for algorithm validation.
