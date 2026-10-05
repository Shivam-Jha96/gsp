# Spike Conventions

Patterns and stack choices established across spike sessions. New spikes follow these unless the question requires otherwise.

## Stack
- **Runtime:** Python 3.11+ / 3.13.
- **Persistence:** PostgreSQL via Supabase connection pool (`DATABASE_URL`, `psycopg2`).
- **Telemetry Layer:** Light-touch DDL with `IF NOT EXISTS` to ensure zero manual migration requirements.
- **Presentation:** Streamlit with custom CSS adhering to permanent dark mode (`#020617` background, `#0f172a` cards, `#38bdf8` cyan accents, `#10b981` emerald accents).

## Structure
- Spikes reside in `.planning/spikes/NNN-descriptive-name/`.
- Each spike contains:
  - `README.md` with YAML frontmatter, Given/When/Then validation, research table, and results.
  - Core implementation module (e.g., `spike_telemetry.py`).
  - Unit test suite (e.g., `test_telemetry.py`).
  - Interactive experiential demo (e.g., `interactive_demo.html`).
  - Verification runner (e.g., `run_spike.py`).

## Patterns
- **Fail-Safe Telemetry:** Telemetry and observability operations must never raise uncaught exceptions that would disrupt trading signal calculation or dashboard rendering.
- **Status Distinction:** Filter queries specifically for `status = 'SUCCESS'` and `completed_at IS NOT NULL` to prevent unverified or crashing runs from corrupting freshness metrics.
- **Timezone Normalization:** Store all timestamps as UTC `TIMESTAMPTZ` in PostgreSQL; convert at presentation boundary to `Asia/Kolkata` (`%H:%M IST`) for local display.
- **Relative Freshness:** Pair absolute time (`13:30 IST`) with relative elapsed context (`5m ago`) and HTML tooltips for instant cognitive recognition of data freshness.
