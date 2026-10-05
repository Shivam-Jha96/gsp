# Spike Manifest

## Ideas

### pipeline-completion-freshness
Durable tracking and dashboard presentation of the completion timestamp of the last successful run of the Global Macro-Sentiment Pipeline (`src/main.py`). Currently, the dashboard displays the latest published timestamp from the news RSS items in `event_signals`, which misleadingly stays fixed at hours-old article publish times (e.g., 05:31 IST) even when the pipeline executes on schedule. By introducing a durable `pipeline_runs` table in PostgreSQL / Supabase, the pipeline records execution lifecycle metrics (started, completed, status, payloads processed), enabling the UI to query and display accurate freshness (`UPDATED HH:MM IST` with relative elapsed time and graceful fallback).

**Requirements:**
- Must record completion timestamp only upon successful completion (`status='SUCCESS'`) of `src/main.py`.
- Must record run telemetry (started_at, completed_at, duration_seconds, items_polled, items_scored, status).
- Must fail safely: pipeline execution and UI rendering must never crash if telemetry table is unreachable.
- Must query the latest successful run in `src/ui/app.py` with sub-millisecond overhead via indexed lookup.
- Must provide graceful backward-compatible fallback to `df_signals['timestamp'].max()` if `pipeline_runs` has no entries.
- Must preserve institutional dark-theme styling for the `UPDATED HH:MM IST` badge, adding elapsed time context on hover/subtext.
- Must auto-create the `pipeline_runs` table (`CREATE TABLE IF NOT EXISTS`) so deployment requires zero manual schema intervention.

## Spikes

| # | Idea | Name | Type | Validates | Verdict | Tags |
|---|------|------|------|-----------|---------|------|
| 001 | pipeline-completion-freshness | pipeline-completion-timestamp | standard | Given a completed run of `src/main.py`, when recorded in `pipeline_runs`, then `src/ui/app.py` renders the exact completion timestamp with relative freshness and graceful fallback | VALIDATED | db, ui, telemetry, pipeline |
