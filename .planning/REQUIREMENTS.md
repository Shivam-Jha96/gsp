# Requirements: Valence

**Defined:** 2026-10-05
**Core Value:** Zero-hallucination, deterministic macroeconomic directional sentiment projection grounded in regional OKF rules with high-performance institutional visualization.

## v1 Requirements

### Baseline & Architecture

- [x] **BASE-01**: News poller fetches global geotargeted RSS feeds across IN, US, UK, JP
- [x] **BASE-02**: Regional affinity classifier validates index tickers and constituents, rejecting contaminants
- [x] **BASE-03**: Canonical fingerprint deduplication prevents redundant processing across 48h windows
- [x] **BASE-04**: Automated OKF engine dynamically refreshes regional macro rules via Gemini AI with model fallback
- [x] **BASE-05**: System-One CLM-8B computes bipolar choice probabilities and continuous directional scores
- [x] **BASE-06**: PostgreSQL client maintains resilient pooled connections with keepalive probes
- [x] **BASE-07**: Signal engine calculates 4-period EMA crossover signals with paper trading dispatch
- [x] **UI-01**: Permanent Dark Mode locked across the Streamlit terminal (theme toggle removed)
- [x] **UI-02**: `@st.fragment` partial re-rendering isolates filter dropdowns and news feed without full-page reloading

### Remediation & Governance (Current Milestone)

- [ ] **QUANT-01**: Eliminate look-ahead leakage in backtest simulation and implement causal timestamp assertions
- [ ] **GOV-01**: Harden Gemini model fallback registry and implement automated OKF Pull Request safety gates
- [ ] **LEDGER-01**: Implement append-only public forward-test ledger tracking daily signals and paper trades
- [ ] **DATA-01**: Ingest direct official Central Bank RSS feeds (Fed, RBI, BoE, BoJ) into the poller

### Modularization & Expansion (Future Milestone)

- [ ] **MOD-01**: Refactor `src/ui/app.py` into dedicated component modules under `src/ui/components/` (header, filters, chart, feed, styling)
- [ ] **MOD-02**: Implement an automated fortnightly GitHub Action to fetch and update `*_constituents.okf.json` files using a free API
- [ ] **TEST-01**: Expand automated unit and regression test coverage for signal EMA crossover and edge case calculation
- [ ] **MON-01**: Integrate proactive health probe reporting across scheduled GitHub Actions pipelines

## v2 Requirements

### Analytics & Strategy

- **STRAT-01**: Multi-asset class cross-asset sentiment correlation (commodities, currencies, equities)
- **STRAT-02**: Historical backtesting engine simulating EMA crossover profitability against benchmark index price action
- **ALERT-01**: Real-time webhook notifications (Telegram / Discord / Slack) for extreme macro sentiment spikes

## Out of Scope

| Feature | Reason |
|---------|--------|
| Light Mode Theme | Explicitly removed to guarantee consistent, high-contrast dark institutional presentation |
| Generative LLM free-text scoring | Introduces temperature hallucinations, prompt drift, and stochastic score distortion |
| Direct live capital order routing | Risk containment; execution restricted to Alpaca Paper Trading |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BASE-01 | Phase 1 | Complete |
| BASE-02 | Phase 1 | Complete |
| BASE-03 | Phase 1 | Complete |
| BASE-04 | Phase 1 | Complete |
| BASE-05 | Phase 1 | Complete |
| BASE-06 | Phase 1 | Complete |
| BASE-07 | Phase 1 | Complete |
| UI-01 | Phase 1 | Complete |
| UI-02 | Phase 1 | Complete |
| QUANT-01 | Phase 2 | Pending |
| GOV-01 | Phase 2 | Pending |
| LEDGER-01 | Phase 2 | Pending |
| DATA-01 | Phase 2 | Pending |
| MOD-01 | Phase 3 | Pending |
| MOD-02 | Phase 3 | Pending |
| TEST-01 | Phase 3 | Pending |
| MON-01 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-05*
*Last updated: 2026-10-05 after initialization*
