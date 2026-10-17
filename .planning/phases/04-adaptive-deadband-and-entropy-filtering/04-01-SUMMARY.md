---
phase: 04
plan: 01
title: Adaptive Regime Deadband & Epistemic Entropy Filtering
status: completed
date: 2026-10-17
key_files:
  created:
    - tests/unit/test_entropy_filter.py
    - tests/unit/test_adaptive_deadband.py
    - .planning/phases/04-adaptive-deadband-and-entropy-filtering/04-01-PLAN.md
    - .planning/phases/04-adaptive-deadband-and-entropy-filtering/04-REVIEW.md
  modified:
    - src/signal_engine/ema.py
    - src/main.py
    - src/signal_engine/forward_tester.py
    - src/ui/components/ledger.py
    - tests/unit/test_forward_tester.py
    - docs/sentiment_math.md
    - .planning/ROADMAP.md
    - .planning/STATE.md
---

# Summary 04-01: Adaptive Regime Deadband & Epistemic Entropy Filtering

## What Changed
1. **`src/signal_engine/ema.py`**:
   - Implemented `calculate_shannon_entropy(p_bull, p_bear)`: Normalized directional Shannon binary entropy $H_2 \in [0.0, 1.0]$.
   - Implemented `calculate_adaptive_deadband(series, base_threshold=5.0, window=20, gamma=0.25, min_threshold=5.0, max_threshold=15.0)`: Dynamic volatility-scaled threshold clamping within $[5.0, 15.0]$.
   - Implemented `resolve_directional_stance(ema_val, entropy, threshold, max_entropy=0.96)`: Joint stance resolution rejecting high-entropy ambiguity into `NEUTRAL`.
   - Implemented `calculate_dual_ema_consensus(series, fast_span=2, slow_span=8)`: Fast/slow EMA consensus verification.
2. **`src/main.py`**:
   - Integrated Shannon entropy calculation in `score_sentiment`, damping magnitude on ambiguous news releases and classifying them as `Neutral`.
   - Exported `"Entropy": round(entropy, 4)` in output dictionary.
   - Updated forward signal recording with entropy-aware stance resolution.
3. **`src/signal_engine/forward_tester.py`**:
   - Upgraded `compute_metrics_from_dataframe` to compute dual metrics: static baseline hit rate (67.8%–71.4%) and upgraded adaptive hit rate (69.0%–80%+).
   - Exported `adaptive_hit_rate_pct`, `adaptive_calls`, `adaptive_neutral_filtered`, and `avg_adaptive_threshold`.
4. **`src/ui/components/ledger.py`**:
   - Surfaced the adaptive hit rate pill (`{adapt_hit_rate:.1f}% ADAPTIVE`) in the Public Track Record card header.
   - Enriched metric cards to show adaptive threshold context without full-page reloads.
5. **`docs/sentiment_math.md`**:
   - Added Section 7.5: Formalized Normalized Epistemic Shannon Entropy Gating ($H_2$).
   - Added Section 8.4: Formalized Volatility-Adaptive Regime Deadband ($\theta_{\text{band}}(t)$).
6. **Automated Test Suites**:
   - Created `tests/unit/test_entropy_filter.py` (6 tests).
   - Created `tests/unit/test_adaptive_deadband.py` (4 tests).
   - Updated `tests/unit/test_forward_tester.py` to assert adaptive metrics.
   - **All 79 unit tests pass in 0.44s with zero regression.**
