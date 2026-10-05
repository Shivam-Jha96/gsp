---
last_mapped_commit: cf96f4d0048d4bf12ec1ec9d2a683bd1077373a2
last_mapped_at: 2026-10-05
---
# Directory Structure & Organization

**Analysis Date:** 2026-10-05

## Directory Layout

```
gsp/
├── .devcontainer/                # Development container definitions
│   └── devcontainer.json
├── .github/                      # GitHub automation & CI/CD workflows
│   └── workflows/
│       ├── ci.yml                # Scheduled 2-hour ingestion & scoring pipeline
│       ├── db_cleanup.yml        # Database pruning & optimization
│       ├── deploy.yml            # Production deployment triggers
│       ├── reclassify_db.yml     # Historical database reclassification
│       └── update_okf.yml        # Scheduled Gemini OKF macroeconomic rule updater
├── .streamlit/                   # Streamlit runtime configuration
│   └── config.toml               # Server, browser, and theme settings
├── docker/                       # Container build files
│   ├── ingestion.Dockerfile      # Headless runner for background ingestion
│   └── ui.Dockerfile             # Streamlit web application container
├── docs/                         # Technical architecture & math specs
│   ├── architecture_and_workflow.md # System flow, pipeline lifecycle, and layer responsibilities
│   ├── build_progress.md         # Historical engineering changelog and milestone log
│   └── sentiment_math.md         # Mathematical formula contracts for CLM probability scoring
├── knowledge/                    # Objective Knowledge Framework (OKF) storage
│   ├── india_constituents.okf.json # Nifty 50 constituent metadata
│   ├── india_macro.okf.md        # India RBI & macroeconomic policy rules
│   ├── japan_constituents.okf.json # Nikkei 225 constituent metadata
│   ├── japan_macro.okf.md        # Bank of Japan macroeconomic policy rules
│   ├── uk_constituents.okf.json  # FTSE 100 constituent metadata
│   ├── uk_macro.okf.md           # Bank of England macroeconomic policy rules
│   ├── us_constituents.okf.json  # S&P 500 constituent metadata
│   └── us_macro.okf.md           # US Federal Reserve macroeconomic policy rules
├── scratch/                      # Temporary prototyping and test scripts
│   ├── query_db.py               # Ad-hoc database queries
│   ├── query_st.py               # Local Streamlit testing probe
│   ├── test_ai.py                # TypeSafe / Modal API smoke test
│   └── test_score.py             # Offline scoring validation
├── scripts/                      # Operational database scripts
│   ├── db_cleanup.py             # Database maintenance and noise pruning
│   └── reclassify_database.py    # Database retroactive affinity correction
├── src/                          # Primary application source code
│   ├── main.py                   # Ingestion and signal engine CLI orchestrator
│   ├── ai_engine/                # AI inference and model wrappers
│   │   ├── context_injector.py   # OKF context injection into prompts
│   │   ├── hf_space/             # Hugging Face Spaces alternative host
│   │   ├── inference.py          # TypeSafe CLM client interface
│   │   └── modal_app.py          # Modal serverless deployment definition
│   ├── config/                   # Declarative market configuration
│   │   ├── asset_classes.json    # Asset class criteria (equity, commodity, etc.)
│   │   ├── market_registry.json  # Regional markets, indices, and locale mapping
│   │   └── market_registry.py    # Registry loaders and helper accessors
│   ├── core/                     # Foundational utilities
│   │   ├── config.py             # Core configuration helpers
│   │   └── logger.py             # Centralized logging setup
│   ├── database/                 # Persistence layer
│   │   ├── client.py             # Resilient Supabase PostgreSQL pool client
│   │   └── schemas.sql           # Database DDL schemas and index definitions
│   ├── hf_space/                 # Alternative deployment assets
│   │   ├── app.py
│   │   └── requirements.txt
│   ├── ingestion/                # Financial news acquisition & validation
│   │   ├── api_clients.py        # External HTTP client helpers
│   │   ├── classifier.py         # RegionalAffinityClassifier (regex scoring engine)
│   │   ├── dedup.py              # NewsDeduplicator & canonical fingerprinting
│   │   └── poller.py             # Async RSS feed polling engine
│   ├── knowledge_engine/         # Automated macroeconomic knowledge management
│   │   └── okf_updater.py        # Google GenAI automated OKF rule updater
│   ├── signal_engine/            # Quantitative strategy and execution
│   │   ├── cron_jobs.py          # EMA crossover signal evaluation & Alpaca routing
│   │   └── ema.py                # Mathematical Exponential Moving Average module
│   └── ui/                       # Frontend presentation layer
│       └── app.py                # Streamlit institutional quantitative terminal
├── tests/                        # Automated test suite
│   ├── backtest/                 # Strategy backtesting modules
│   ├── integration/              # External service integration tests
│   │   └── test_modal.py         # Modal serverless API smoke test
│   └── unit/                     # Fast deterministic unit tests
│       ├── test_classifier_and_registry.py # Affinity classifier & registry tests
│       ├── test_dedup_and_sentiment.py     # Deduplication and sentiment math tests
│       └── test_okf_updater.py             # Dynamic model discovery & fallback tests
├── .gitignore                    # Git ignore file
├── README.md                     # Project overview and deployment guide
└── requirements.txt              # Primary project dependencies
```

## Key File Locations & Roles

- **Core Orchestrator:** `src/main.py` - Runs ingestion, filtering, scoring, persistence, and signal generation in a single command.
- **Frontend App:** `src/ui/app.py` - Single-file reactive Streamlit application implementing institutional terminal UI.
- **Database Engine:** `src/database/client.py` and `src/database/schemas.sql` - Connection pooling and data models.
- **Regional Filtering Engine:** `src/ingestion/classifier.py` - Prevents cross-region news contamination.
- **Deduplication Engine:** `src/ingestion/dedup.py` - Normalizes and dedups news across multiple queries.
- **Market Knowledge Base:** `knowledge/*.okf.md` - Institutional macro rules driving AI context.

## Naming Conventions

- **Python Modules:** Lowercase with underscores (`market_registry.py`, `okf_updater.py`).
- **Classes:** PascalCase (`RegionalAffinityClassifier`, `SupabasePoolClient`, `NewsDeduplicator`).
- **Functions & Variables:** snake_case (`score_sentiment`, `canonical_fingerprint`, `load_okf_rules`).
- **Configuration & Knowledge Files:** lowercase with underscores and descriptive extensions (`india_macro.okf.md`, `india_constituents.okf.json`).
- **Tests:** Prefixed with `test_` matching target modules (`test_classifier_and_registry.py`).

---

*Structure analysis: 2026-10-05*
*Update when directories or files are rearranged*
