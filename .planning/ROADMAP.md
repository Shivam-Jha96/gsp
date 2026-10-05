# Roadmap: Global Sentiment Platform of Share Markets (GSP)

## Overview

GSP provides real-time quantitative macroeconomic directional sentiment calculation across four major global equity hubs (India, US, UK, Japan). This milestone organizes the platform into two clear phases: Phase 1 captures the complete validated baseline (ingestion, regex classification, deduplication, Gemini OKF rule updating, System-One CLM-8B probability scoring, resilient database pooling, EMA paper trading, and the permanently dark-themed reactive Streamlit dashboard). Phase 2 focuses on modular architectural refactoring, comprehensive test suites, and operational pipeline health probes.

## Phases

- [x] **Phase 1: Baseline Quantitative Platform & Permanent Dark Theme** - End-to-end ingestion, AI scoring, database pooling, and permanent dark terminal
- [ ] **Phase 2: UI Component Modularization & Operational Hardening** - Modularize `app.py` into `src/ui/components/`, expand EMA test suites, and add pipeline monitoring

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

### Phase 2: UI Component Modularization & Operational Hardening
**Goal**: Refactor single-file UI monolith into maintainable component packages and harden test coverage
**Depends on**: Phase 1
**Requirements**: MOD-01, TEST-01, MON-01
**Success Criteria**:
  1. `src/ui/app.py` is decomposed into cleanly scoped components in `src/ui/components/` (header, toolbar, chart, feed, styling).
  2. Automated test suite expands to cover multi-window EMA calculations and paper trading triggers.
  3. Scheduled GitHub Actions workflows include automated health probes reporting pipeline availability.
**Plans**: 2 plans

Plans:
- [ ] 02-01: Decompose `app.py` into `src/ui/components/` maintaining all CSS variables and fragment reactivity
- [ ] 02-02: Expand test coverage and add CI pipeline monitoring

## Progress

**Execution Order:**
Phase 1 (Complete) → Phase 2 (Ready to plan)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Baseline Quantitative Platform & Permanent Dark Theme | 3/3 | Complete | 2026-10-05 |
| 2. UI Component Modularization & Operational Hardening | 0/2 | Ready to plan | - |

---
*Roadmap defined: 2026-10-05*
*Last updated: 2026-10-05 after initialization*
