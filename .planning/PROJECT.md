# Global Sentiment Platform of Share Markets (GSP)

## What This Is

Global Sentiment Platform of Share Markets (GSP) is an institutional-grade quantitative macroeconomic sentiment and directional signal engine. It ingests global financial news, filters regional affinity and noise via compiled regex classifiers and fingerprint deduplication, generates continuous directional sentiment scores using serverless Contrastive Language Models (CLM-8B System-One), and presents live multi-index surfaces on a permanently dark-themed reactive Streamlit dashboard.

## Core Value

Zero-hallucination, deterministic macroeconomic directional sentiment projection grounded in regional Objective Knowledge Framework (OKF) rules, coupled with ultra-low latency interactive multi-market visualization.

## Requirements

### Validated

- ✓ Real-time multi-region news ingestion (India, US, UK, Japan) with geotargeted queries — existing
- ✓ Pre-compiled regex regional affinity classification with constituent matching — existing
- ✓ Alpha-numeric canonical headline deduplication across 48h windows — existing
- ✓ Automated macroeconomic OKF rule updates via Google Gemini AI with fallback pools — existing
- ✓ Contrastive-LM (CLM-8B) probability scoring with relative spread and neutrality attenuation — existing
- ✓ Resilient PostgreSQL/Supabase connection pooling with keepalive probes and dead connection recycling — existing
- ✓ 4-period Exponential Moving Average (EMA) crossover signal engine with Alpaca paper trading — existing
- ✓ Institutional Streamlit terminal with `@st.fragment` partial re-rendering — existing
- ✓ Permanent Dark Theme enforcement (theme toggle removed) — 2026-10-05

### Active

- [ ] UI Component modularization (`src/ui/components/`) to refactor monolithic `app.py`
- [ ] Strategy backtesting engine extension for multi-asset class EMA crossovers
- [ ] Automated end-to-end integration monitoring across scheduled GitHub Actions pipelines

### Out of Scope

- Light mode theme — Explicitly removed; terminal is locked permanently into dark mode for high-contrast institutional trading aesthetics.
- Unconstrained generative LLM free-text sentiment scoring — Excluded to eliminate prompt drift, temperature hallucinations, and confidence clustering.

## Context

- **Backend Architecture:** Decoupled Python services running ingestion, classification, knowledge maintenance, and signal generation.
- **Persistence:** Supabase PostgreSQL with vertical partitioning (`event_signals` math layer, `event_payloads` document layer).
- **Frontend:** Streamlit 1.65.0 with custom dark-themed CSS, Plotly time-series surface, and segmented sentiment filtering pills.
- **Automation:** Scheduled GitHub Actions runners (`ci.yml`, `update_okf.yml`, `db_cleanup.yml`).

## Constraints

- **Theme**: Always in permanent dark mode (`#020617` background, `#0f172a` cards, `#10b981` / `#ef4444` directional accents).
- **API Quotas**: Strict compliance with Google Gemini free-tier 15 RPM quota (pacing interval >= 6.0s).
- **Latency**: Sub-second UI updates via `@st.fragment` isolation without full-page reloads.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Permanently enforce Dark Mode | High-contrast visual clarity for quant trading dashboards; avoids dual-theme CSS fragmentation | ✓ Good |
| Contrastive LM over Generative LLM | Bipolar choice probabilities eliminate hallucinations and inverse bias | ✓ Good |
| Segmented Fragment Rendering | Dropdowns update dashboard without triggering full script re-runs | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-05 after initialization*
