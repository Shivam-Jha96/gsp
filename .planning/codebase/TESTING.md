---
last_mapped_commit: cf96f4d0048d4bf12ec1ec9d2a683bd1077373a2
last_mapped_at: 2026-10-05
---
# Testing Practices & Structure

**Analysis Date:** 2026-10-05

## Test Framework & Execution

**Framework:**
- Python standard library `unittest`.
- Zero additional testing dependencies required (operates in standard lightweight CI environments).

**Execution Commands:**

```bash

# Run all unit tests

python -m unittest discover tests

# Run specific test suite

python -m unittest tests/unit/test_classifier_and_registry.py
python -m unittest tests/unit/test_dedup_and_sentiment.py
python -m unittest tests/unit/test_okf_updater.py

# Run integration tests (requires network/API keys)

python -m unittest tests/integration/test_modal.py
```

## Test Directory Organization

```
tests/
├── backtest/                           # Backtesting framework and strategy simulation
│   └── __init__.py
├── integration/                        # Live API & external service integration tests
│   ├── __init__.py
│   └── test_modal.py                   # Modal CLM endpoint health & live response verification
└── unit/                               # Fast, deterministic, zero-network unit tests
    ├── __init__.py
    ├── test_classifier_and_registry.py # Comprehensive market registry & affinity classifier validation
    ├── test_dedup_and_sentiment.py     # Canonical fingerprinting, deduplicator, and sentiment math
    └── test_okf_updater.py             # Model discovery, rate limiter pacing, and fallback mechanics
```

## Unit Test Coverage Breakdown

**1. Market Registry & Affinity Classifier (`test_classifier_and_registry.py`):**
- `test_market_registry_structure`: Validates all 4 regions (IN, US, UK, JP) have valid currency, locales, minimum 3 indices, 5 anchors, and valid OKF markdown files.
- `test_build_rss_feeds`: Validates URL generation, geotargeting query strings (`gl`, `hl`, `ceid`), and ticker mappings.
- `test_classifier_valid_regional_acceptance`: Validates that valid headlines for IN, US, UK, JP are correctly identified and accepted.
- `test_classifier_cross_region_rejection`: Verifies that cross-region contaminants (e.g., Indian shares pulled under UK feeds, US tech selloffs pulled under India) and non-market noise (crime, celebrity) are rejected.
- `test_classifier_constituent_company_recognition`: Validates that individual constituent companies (e.g., Mulberry, Fidelity, Moderna, TCS, Toyota) correctly resolve to their benchmark indices.
- `test_classifier_broad_market_equity_action`: Validates that broad market news without specific country names is properly accepted under regional market vocabulary heuristics.

**2. Deduplication & Sentiment Math (`test_dedup_and_sentiment.py`):**
- Tests `clean_headline_text()` for HTML unescaping and publisher suffix trimming (`- Reuters`, `| Bloomberg`).
- Tests `canonical_fingerprint()` for punctuation and case invariance.
- Tests `NewsDeduplicator` intra-batch and cross-batch filtering.
- Tests mathematical edge cases for relative directional spread $S_{rel}$ and neutrality attenuation.

**3. OKF Updater (`test_okf_updater.py`):**
- Tests `get_available_models()` with mock API clients and static fallback activation under rate limits.
- Tests `rate_limited_generate()` pacing intervals to verify quota compliance.

## Mocking & Isolation Strategy

- Unit tests are completely decoupled from external network access, live database connections, and paid AI APIs.
- Data structures (`registry`, `constituents`, `payloads`) are loaded directly from repository fixtures (`src/config/`, `knowledge/`).
- Integration tests (`test_modal.py`) are separated and run on-demand with appropriate credentials.

---

*Testing analysis: 2026-10-05*
*Update when testing strategy or tools change*
