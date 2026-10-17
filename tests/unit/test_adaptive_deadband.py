"""
Unit tests for Volatility-Adaptive Regime Deadband in Valence Signal Engine.
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from signal_engine.ema import calculate_adaptive_deadband, calculate_dual_ema_consensus, resolve_directional_stance


class TestAdaptiveDeadband(unittest.TestCase):
    def test_scalar_threshold(self):
        th = calculate_adaptive_deadband(5.0)
        self.assertEqual(th, 5.0)
        
        # Test scalar clamping
        th_low = calculate_adaptive_deadband(2.0, min_threshold=5.0)
        self.assertEqual(th_low, 5.0)

    def test_series_flat_variance_minimum_threshold(self):
        # Perfectly flat series (zero std) -> minimum threshold
        flat = pd.Series([10.0] * 30)
        th_series = calculate_adaptive_deadband(flat, base_threshold=5.0, min_threshold=5.0)
        self.assertTrue((th_series == 5.0).all())

    def test_series_high_variance_expansion(self):
        # Volatile series with high standard deviation
        np.random.seed(42)
        volatile = pd.Series(np.random.normal(0, 30.0, size=50))
        th_series = calculate_adaptive_deadband(volatile, base_threshold=5.0, gamma=0.25, min_threshold=5.0, max_threshold=15.0)
        
        # Upper values should expand above 5.0 due to volatility
        self.assertGreater(th_series.max(), 5.0)
        # Should strictly respect clamping boundary
        self.assertLessEqual(th_series.max(), 15.0)
        self.assertGreaterEqual(th_series.min(), 5.0)

    def test_dual_ema_consensus(self):
        # Upward trending series
        trend = pd.Series(np.linspace(0, 50, 20))
        fast, slow, stance = calculate_dual_ema_consensus(trend, fast_span=2, slow_span=8, base_threshold=5.0)
        
        # Fast EMA should lead slow EMA
        self.assertGreater(fast.iloc[-1], slow.iloc[-1])
        # In established uptrend, stance should be BULLISH
        self.assertEqual(stance.iloc[-1], "BULLISH")
        
        # Downward trending series
        downtrend = pd.Series(np.linspace(0, -50, 20))
        fast_d, slow_d, stance_d = calculate_dual_ema_consensus(downtrend, fast_span=2, slow_span=8, base_threshold=5.0)
        self.assertEqual(stance_d.iloc[-1], "BEARISH")


if __name__ == "__main__":
    unittest.main()
