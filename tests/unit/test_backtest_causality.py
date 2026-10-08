"""
Unit tests for Valence Backtesting Engine Causality & Point-in-Time Integrity.
Verifies:
1. No future data / look-ahead leakage in strategy decisions.
2. Invariance to future price shocks prior to event bar.
3. Information Coefficient causal alignment.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

import numpy as np
import pandas as pd
from benchmark.backtest_engine import ValenceBacktestEngine, generate_mock_price_series


class TestBacktestCausality(unittest.TestCase):
    def setUp(self):
        self.engine = ValenceBacktestEngine(
            initial_capital=100000.0,
            slippage_bps=5.0,
            fee_bps=1.0,
            bullish_threshold=5.0,
            bearish_threshold=-5.0,
            ema_window=4
        )

    def test_causal_invariance_to_future_price_shocks(self):
        """
        Tests that an extreme future price movement at time t+K does NOT affect
        the strategy positions or sentiment scores at time t < t+K.
        """
        df_base = generate_mock_price_series(periods=60, start_price=100.0)
        df_shock = df_base.copy()
        
        # Inject an extreme price shock at bar 45
        shock_bar = 45
        df_shock.iloc[shock_bar:, df_shock.columns.get_loc("close")] *= 2.5
        df_shock.iloc[shock_bar:, df_shock.columns.get_loc("open")] *= 2.5
        
        res_base = self.engine.run_backtest(df_base)
        res_shock = self.engine.run_backtest(df_shock)
        
        # Extract positions prior to the shock bar
        positions_base = res_base["data"]["position"].values
        positions_shock = res_shock["data"]["position"].values
        
        # Positions strictly prior to the shock bar MUST be identical
        np.testing.assert_array_equal(
            positions_base[:shock_bar],
            positions_shock[:shock_bar],
            err_msg="Look-ahead leakage detected: future price shock mutated historical strategy positions!"
        )

    def test_information_coefficient_bounds(self):
        """
        Tests that random causal noise yields an Information Coefficient within realistic bounds.
        """
        df = generate_mock_price_series(periods=100, start_price=500.0)
        res = self.engine.run_backtest(df)
        summary = res["summary"]
        
        ic = summary["information_coefficient"]
        # IC of causal simulation without look-ahead should be modest (typically < 0.20)
        self.assertLess(abs(ic), 0.25, f"IC {ic} is unrealistically high, indicating possible look-ahead leakage")

    def test_deterministic_causal_simulation(self):
        """
        Tests that repeated backtests on identical price series produce bitwise identical results.
        """
        df = generate_mock_price_series(periods=50, start_price=200.0)
        res1 = self.engine.run_backtest(df)
        res2 = self.engine.run_backtest(df)
        
        self.assertEqual(res1["summary"]["final_equity_strategy"], res2["summary"]["final_equity_strategy"])
        self.assertEqual(res1["summary"]["sharpe_ratio_strategy"], res2["summary"]["sharpe_ratio_strategy"])


if __name__ == "__main__":
    unittest.main()
