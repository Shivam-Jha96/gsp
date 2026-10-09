import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

import numpy as np
import pandas as pd


from benchmark.predictive_metrics import (
    calculate_information_coefficient,
    calculate_rank_information_coefficient,
    calculate_directional_hit_rate,
    calculate_expected_calibration_error,
    calculate_brier_score,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_calmar_ratio,
    calculate_granger_causality,
    test_granger_causality,
)


class TestBenchmarkMetrics(unittest.TestCase):
    def test_information_coefficient_perfect_positive(self):
        signals = [10.0, 20.0, 30.0, 40.0, 50.0]
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]
        ic = calculate_information_coefficient(signals, returns)
        self.assertAlmostEqual(ic, 1.0, places=4)

    def test_information_coefficient_perfect_negative(self):
        signals = [50.0, 40.0, 30.0, 20.0, 10.0]
        returns = [0.01, 0.02, 0.03, 0.04, 0.05]
        ic = calculate_information_coefficient(signals, returns)
        self.assertAlmostEqual(ic, -1.0, places=4)

    def test_information_coefficient_zero_variance(self):
        signals = [10.0, 10.0, 10.0]
        returns = [0.01, 0.02, 0.03]
        ic = calculate_information_coefficient(signals, returns)
        self.assertEqual(ic, 0.0)

    def test_rank_information_coefficient(self):
        signals = [10.0, 50.0, 30.0, 40.0, 20.0]
        returns = [0.01, 0.05, 0.03, 0.04, 0.02]
        rank_ic = calculate_rank_information_coefficient(signals, returns)
        self.assertAlmostEqual(rank_ic, 1.0, places=4)

    def test_directional_hit_rate(self):
        signals = [10.0, -20.0, 30.0, -40.0]
        returns = [0.02, -0.01, -0.05, -0.03] # 3 match (10 & 0.02, -20 & -0.01, -40 & -0.03)
        hit_rate = calculate_directional_hit_rate(signals, returns)
        self.assertAlmostEqual(hit_rate, 0.75, places=4)

    def test_expected_calibration_error(self):
        # Perfectly calibrated: 10 samples with 0.8 confidence, exactly 8 correct
        confidences = [0.8] * 10
        predictions = ["Bullish"] * 10
        true_labels = ["Bullish"] * 8 + ["Bearish"] * 2
        ece = calculate_expected_calibration_error(confidences, predictions, true_labels, n_bins=5)
        self.assertAlmostEqual(ece, 0.0, places=4)

    def test_brier_score_perfect(self):
        # Perfect probabilities
        probs = [
            {"Bullish": 1.0, "Bearish": 0.0, "Neutral": 0.0},
            {"Bullish": 0.0, "Bearish": 1.0, "Neutral": 0.0},
            {"Bullish": 0.0, "Bearish": 0.0, "Neutral": 1.0},
        ]
        labels = ["Bullish", "Bearish", "Neutral"]
        brier = calculate_brier_score(probs, labels)
        self.assertAlmostEqual(brier, 0.0, places=4)

    def test_sharpe_and_sortino_ratio(self):
        # Positive steady returns
        returns = [0.01, 0.015, 0.008, 0.012, 0.02]
        sharpe = calculate_sharpe_ratio(returns, periods_per_year=252)
        self.assertGreater(sharpe, 0.0)

        sortino = calculate_sortino_ratio(returns, periods_per_year=252)
        # All returns > 0, so downside std is 0 -> returns 0.0 or high
        self.assertIsInstance(sortino, float)

    def test_max_drawdown(self):
        # Peak 100 -> 120 -> 90 -> 110 (Peak is 120, trough is 90 -> DD = (120 - 90) / 120 = 25% = 0.25)
        equity = [100.0, 120.0, 90.0, 110.0]
        max_dd, peak_idx, trough_idx = calculate_max_drawdown(equity)
        self.assertAlmostEqual(max_dd, 0.25, places=4)
        self.assertEqual(peak_idx, 1)
        self.assertEqual(trough_idx, 2)

    def test_calmar_ratio(self):
        cagr = 0.30
        max_dd = 0.15
        calmar = calculate_calmar_ratio(cagr, max_dd)
        self.assertAlmostEqual(calmar, 2.0, places=4)

    def test_granger_causality_structure(self):
        np.random.seed(42)
        sentiment = np.random.normal(0, 1, 50)
        returns = np.random.normal(0, 0.02, 50)
        res = calculate_granger_causality(sentiment, returns, max_lag=2)
        self.assertIn("f_stat", res)
        self.assertIn("p_value", res)
        self.assertIn("is_causal", res)
        
        # Test backward compatibility alias
        res_alias = test_granger_causality(sentiment, returns, max_lag=2)
        self.assertEqual(res["f_stat"], res_alias["f_stat"])


if __name__ == "__main__":
    unittest.main()
