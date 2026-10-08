# Roadmap: Valence

## Overview

Valence provides real-time quantitative macroeconomic directional sentiment calculation across four major global equity hubs (India, US, UK, Japan). This milestone organizes the platform into two clear phases: Phase 1 captures the complete validated baseline (ingestion, regex classification, deduplication, Gemini OKF rule updating, System-One CLM-8B probability scoring, resilient database pooling, EMA paper trading, and the permanently dark-themed reactive Streamlit dashboard). Phase 2 focuses on modular architectural refactoring, comprehensive test suites, and operational pipeline health probes.

## Phases

- [x] **Phase 1: Baseline Quantitative Platform & Permanent Dark Theme** - End-to-end ingestion, AI scoring, database pooling, and permanent dark terminal
- [x] **Phase 2: Quantitative Engine Remediation, Governance & Public Forward Testing** - Eliminate look-ahead leakage, update Gemini model fallbacks, implement OKF PR safety gates, and launch append-only forward-test ledger
- [ ] **Phase 3: UI Component Modularization & Operational Hardening** - Modularize `app.py` into `src/ui/components/`, expand EMA test suites, and add pipeline monitoring

## Phase Details

### Phase 1: Baseline Quantitative Platform & Permanent Dark Theme
**Goal**: Deliver a reliable, deterministic quantitative sentiment engine and high-contrast institutional dark dashboard
**Depends on**: Nothing (established brownfield baseline)
**Requirements**: BASE-01, BASE-02, BASE-03, BASE-04, BASE-05, BASE-06, BASE-07, UI-01, UI-02
**Success Criteria**:
  1. Geotargeted multi-region RSS news is parsed, deduplicated, and filtered without cross-region contamination.
  2. Bipolar CLM-8B System-One probability projections produce continuous directional sentiment in `[-1.0, 1.0]`.
  3. Supabase PostgreSQL pool sustains idle connections without disconnect exceptions.
  4. Streamlit terminal is permanently in Dark Mode with theme toggle removed and header card centered.
  5. Filter dropdowns update live charts and news feed via `@st.fragment` without full-page reloads.
**Plans**: 3 plans (all complete)

Plans:
- [x] 01-01: Core ingestion pipeline, regex affinity classifier, and canonical fingerprinting
- [x] 01-02: TypeSafe CLM-8B inference, OKF rule engine, and Supabase connection pooler
- [x] 01-03: Reactive Streamlit dashboard with partial fragments and permanent dark theme

### Phase 2: Quantitative Engine Remediation, Governance & Public Forward Testing
**Goal**: Remediate external review findings by eliminating look-ahead backtest leakage, hardening Gemini model fallbacks, implementing OKF PR safety gates, and launching a public forward-test ledger with licensable data.
**Depends on**: Phase 1
**Requirements**: QUANT-01, GOV-01, LEDGER-01, DATA-01
**Success Criteria**:
  1. `src/benchmark/backtest_engine.py` eliminates future price return look-ahead leakage and enforces causal point-in-time assertions.
  2. `src/benchmark/nlp_evaluator.py` measures authentic network latency percentiles rather than local in-memory simulation loops.
  3. `src/knowledge_engine/okf_updater.py` updates to active Gemini 2.5/3.x models, removes deprecated endpoints, and implements automated PR generation for macro rule shifts.
  4. Database schema adds `published_at`, `scored_at`, and `okf_version_hash` audit metadata.
  5. Append-only `reports/forward_test_ledger.csv` tracks daily out-of-sample forward signals and paper trading execution.
  6. Official Central Bank RSS feeds (Fed, RBI, BoE, BoJ) are integrated into the ingestion pipeline.
**Plans**: 3 plans

Plans:
- [x] 02-01: Benchmarking Suite & Backtest Look-Ahead Remediation (Plan 2.2)
- [x] 02-02: Pipeline Hardening, Model Fallback Registry & OKF Governance (Plan 2.3)
- [x] 02-03: Public Forward-Testing Ledger & Central Bank Feed Ingestion (Plan 2.4)

### Phase 3: UI Component Modularization & Operational Hardening
**Goal**: Refactor single-file UI monolith into maintainable component packages and harden test coverage
**Depends on**: Phase 2
**Requirements**: MOD-01, TEST-01, MON-01
**Success Criteria**:
  1. `src/ui/app.py` is decomposed into cleanly scoped components in `src/ui/components/` (header, toolbar, chart, feed, styling).
  2. Automated test suite expands to cover multi-window EMA calculations and paper trading triggers.
  3. Scheduled GitHub Actions workflows include automated health probes reporting pipeline availability.
**Plans**: 2 plans

Plans:
- [ ] 03-01: Decompose `app.py` into `src/ui/components/` maintaining all CSS variables and fragment reactivity
- [ ] 03-02: Expand test coverage and add CI pipeline monitoring

## Progress

**Execution Order:**
Phase 1 (Complete) → Phase 2 (Complete) → Phase 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline Quantitative Platform & Permanent Dark Theme | 3/3 | Complete | 2026-10-05 |
| 2. Quantitative Engine Remediation, Governance & Public Forward Testing | 3/3 | Complete | 2026-10-08 |
| 3. UI Component Modularization & Operational Hardening | 0/2 | Pending | - |

---
*Roadmap defined: 2026-10-05*
*Last updated: 2026-10-08 with review remediation milestone*
