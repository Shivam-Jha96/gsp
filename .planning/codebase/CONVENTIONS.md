---
last_mapped_commit: cf96f4d0048d4bf12ec1ec9d2a683bd1077373a2
last_mapped_at: 2026-10-05
---
# Coding Conventions & Patterns

**Analysis Date:** 2026-10-05

## Code Style & Formatting

**Language & Standards:**
- **Standard:** PEP 8 Python style conventions.
- **Typing:** Extensive use of Python standard library `typing` (`Optional`, `Dict`, `List`, `Tuple`, `Any`, `Set`) across core business logic (e.g. `src/ingestion/classifier.py`, `src/ingestion/dedup.py`).
- **Imports:** Structured in logical groupings:
  1. Standard library imports (`os`, `sys`, `re`, `html`, `logging`, `asyncio`, `time`).
  2. Third-party packages (`streamlit`, `pandas`, `plotly`, `psycopg2`, `typesafe_sdk`, `google.genai`).
  3. Internal application packages (`config.market_registry`, `ingestion.dedup`, `database.client`).
  4. Resilient path resolution via `sys.path.insert(0, ...)` to ensure multi-runtime compatibility across Streamlit Cloud, local execution, and Docker containers.

## Design Patterns & Idioms

**1. Declarative Registry Pattern (`src/config/market_registry.py`):**
- System configuration (regions, indices, tickers, economic anchors, currency, locales) is stored declaratively in `src/config/market_registry.json`.
- Python helper functions (`load_market_registry()`, `get_region_meta()`, `build_rss_feeds()`) expose clean, immutable accessors to decouple market definitions from business logic.

**2. Compiled Regex Boundary Optimization (`src/ingestion/classifier.py`):**
- Pattern matching for index tickers, constituent names, and economic anchors are pre-compiled into regexes with word boundaries (`\b(?:...)\b`) during `__init__()`.
- Sorted by token length descending to ensure specific multi-word tokens match before shorter substrings.

**3. Singleton Connection Pooling with Pre-Checkout Health Checks (`src/database/client.py`):**
- Singleton accessor `get_db_client()` manages a thread-safe `psycopg2.pool.ThreadedConnectionPool`.
- Context manager `get_connection()` checks `_is_alive(conn)` via lightweight `SELECT 1` queries before granting connections.
- Broken or disconnected sockets are evicted via `pool.putconn(conn, close=True)` to prevent pool poisoning.

**4. Reactive Fragment Tree Isolation (`src/ui/app.py`):**
- Heavy UI containers that receive user interactions (e.g., filter dropdowns, news stream sentiment pills) are wrapped in `@st.fragment` functions.
- Prevents expensive top-to-bottom script re-execution, database reloading, and style re-computation on user widget changes.

**5. Multi-Tiered AI Resilience & Model Fallbacks (`src/knowledge_engine/okf_updater.py`):**
- Dynamic account-level model capability inspection (`client.models.list()`) combined with structured priority lists.
- Strict pacing via rate-guards (`MIN_REQUEST_INTERVAL = 6.0s`) to stay deterministically under free-tier API quotas.

## Error Handling & Logging

**Logging Standard:**
- Built-in `logging` module configured with timestamps and level: `logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")`.
- Structured tags inside log statements for rapid debugging:
  - `[CLASSIFIER: ACCEPT-BROAD-MARKET]`
  - `[CLASSIFIER: REJECT-CONTAMINANT]`
  - `[CLASSIFIER: RE-ROUTE]`
  - `[RATE-GUARD]`
  - `[QUOTA/429]`

**Defensive Programming:**
- External API calls and LLM outputs are defensive against payload variations:
  - Validates dictionary vs list outputs.
  - Clamps numerical scores within mathematical limits `[-1.0, 1.0]`.
  - Normalizes probabilities to ensure $\sum P_i = 1.0$.

---

*Conventions analysis: 2026-10-05*
*Update when conventions or standards evolve*
