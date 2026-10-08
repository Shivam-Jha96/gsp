# Valence Institutional Benchmark Report
**Generated**: 2026-10-08 06:33:48 UTC  
**Classification**: Production Quantitative Architecture Validation

---

## 1. Executive Summary
This report formalizes the benchmark results of the **Valence Quantitative Macroeconomic Sentiment Engine** across all four operational tiers:
- **Tier 1 (NLP Calibration)**: Evaluates System-One CLM against academic and dictionary baselines.
- **Tier 2 (Ingestion & Filtering)**: Evaluates Regional Affinity and Canonical Fingerprint deduplication.
- **Tier 3 (Alpha & Backtesting)**: Evaluates predictive alpha, Information Coefficient (IC), and trading returns.
- **Tier 4 (Infrastructure & UI)**: Evaluates database query performance and reactive UI latency.

---

## 4. Tier 3: Quantitative Alpha & Historical Backtest
| Performance Metric | Valence 4-Period EMA Strategy | Buy & Hold Benchmark | Delta / Spread |
| :--- | :--- | :--- | :--- |
| **Total Net Return** | **-20.13%** | 2.82% | **-22.95%** |
| **Annualized Return (CAGR)** | **-44.26%** | 7.49% | **-51.75%** |
| **Sharpe Ratio** | **-9.78** | 0.7 | **+-10.48** |
| **Sortino Ratio** | **-7.79** | — | — |
| **Maximum Drawdown** | **20.71%** | 4.53% | **-16.18% improvement** |
| **Calmar Ratio** | **-2.14** | — | — |
| **Win Rate** | **35.62%** | — | (Profit Factor: 0.37) |
| **Information Coefficient (IC)** | **-0.0253** | — | Rank IC: -0.0048 |
| **Directional Hit Rate** | **51.35%** | — | Target > 55.0% |

---

