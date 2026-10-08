"""
Unit tests for the Valence Signal Engine:
- Multi-window EMA recursive calculations (e.g., 4-period, 12-period).
- Deadband filter bounds (+/- 5.0) and transition regimes.
- Strict execution lockout when ENABLE_TRADE_EXECUTION=false.
"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from src.signal_engine.ema import calculate_ema
from src.signal_engine.cron_jobs import execute_signal
from src.signal_engine.forward_tester import compute_metrics_from_dataframe


class TestSignalEngineEMA(unittest.TestCase):
    """Verifies mathematical correctness of multi-window recursive EMA calculations."""

    def setUp(self):
        self.sample_scores = [10.0, 20.0, 30.0, 40.0]
        self.df = pd.DataFrame({"sentiment_score": self.sample_scores})

    def test_ema_4_period_recursive_calculation(self):
        """
        Verify span=4 EMA against exact manual recursion:
        alpha = 2 / (4 + 1) = 0.4
        EMA_0 = 10.0
        EMA_1 = 0.4 * 20.0 + 0.6 * 10.0 = 14.0
        EMA_2 = 0.4 * 30.0 + 0.6 * 14.0 = 20.4
        EMA_3 = 0.4 * 40.0 + 0.6 * 20.4 = 28.24
        """
        ema = calculate_ema(self.df, window=4, column="sentiment_score")
        self.assertAlmostEqual(ema.iloc[0], 10.0, places=4)
        self.assertAlmostEqual(ema.iloc[1], 14.0, places=4)
        self.assertAlmostEqual(ema.iloc[2], 20.4, places=4)
        self.assertAlmostEqual(ema.iloc[3], 28.24, places=4)

    def test_ema_12_period_recursive_calculation(self):
        """
        Verify span=12 EMA against exact manual recursion:
        alpha = 2 / (12 + 1) = 2 / 13 ~ 0.15384615
        EMA_0 = 10.0
        EMA_1 = alpha * 20.0 + (1 - alpha) * 10.0 = 10.0 + alpha * 10.0 = 11.53846
        EMA_2 = alpha * 30.0 + (1 - alpha) * EMA_1
        """
        alpha_12 = 2.0 / 13.0
        expected_0 = 10.0
        expected_1 = alpha_12 * 20.0 + (1.0 - alpha_12) * expected_0
        expected_2 = alpha_12 * 30.0 + (1.0 - alpha_12) * expected_1
        expected_3 = alpha_12 * 40.0 + (1.0 - alpha_12) * expected_2

        ema = calculate_ema(self.df, window=12, column="sentiment_score")
        self.assertAlmostEqual(ema.iloc[0], expected_0, places=4)
        self.assertAlmostEqual(ema.iloc[1], expected_1, places=4)
        self.assertAlmostEqual(ema.iloc[2], expected_2, places=4)
        self.assertAlmostEqual(ema.iloc[3], expected_3, places=4)

    def test_ema_custom_column_and_index(self):
        """Test calculation with custom column name and datetime index."""
        dates = pd.date_range("2026-10-01", periods=4, freq="h", tz="UTC")
        df_custom = pd.DataFrame({"sentiment_index": [50.0, 75.0, 25.0, 90.0]}, index=dates)
        ema = calculate_ema(df_custom, window=4, column="sentiment_index")
        self.assertEqual(len(ema), 4)
        self.assertTrue((ema.index == dates).all())

    def test_ema_invalid_inputs_raise_errors(self):
        """Ensure defensive type and column validation."""
        with self.assertRaises(TypeError):
            calculate_ema([1, 2, 3])  # type: ignore

        with self.assertRaises(ValueError):
            calculate_ema(self.df, column="non_existent_col")


class TestSignalEngineDeadband(unittest.TestCase):
    """Verifies deadband filtering boundaries (+/- 5.0) and transition regimes."""

    def test_deadband_filter_metrics(self):
        """
        Tests that signals within the [-5.0, 5.0] deadband are classified as neutral
        and filtered out from directional hit-rate calculations.
        """
        now = pd.Timestamp.now("UTC")
        dates = pd.date_range(end=now, periods=5, freq="h")
        
        # 3 signals inside deadband (-3.0, 2.0, 4.9), 2 signals outside (15.0, -20.0)
        df_deadband = pd.DataFrame({
            "timestamp": dates,
            "index_ticker": ["SPY"] * 5,
            "sentiment_index": [15.0, -3.0, 2.0, 4.9, -20.0]
        })

        metrics = compute_metrics_from_dataframe(df_deadband)
        self.assertEqual(metrics["record_count"], 5)
        # Only values outside [-5.0, 5.0] EMA become directional calls
        self.assertGreater(metrics["directional_calls"], 0)
        self.assertGreater(metrics["neutral_filtered"], 0)
        self.assertEqual(metrics["directional_calls"] + metrics["neutral_filtered"], 5)

    def test_pure_deadband_zero_directional_calls(self):
        """When all signals are strictly within deadband [-5.0, 5.0], directional_calls must be 0."""
        dates = pd.date_range("2026-10-01", periods=3, freq="h", tz="UTC")
        df_flat = pd.DataFrame({
            "timestamp": dates,
            "index_ticker": ["SPY"] * 3,
            "sentiment_index": [1.0, -2.0, 0.5]
        })
        metrics = compute_metrics_from_dataframe(df_flat)
        self.assertEqual(metrics["directional_calls"], 0)
        self.assertEqual(metrics["neutral_filtered"], 3)


class TestSignalEngineExecutionLockout(unittest.TestCase):
    """Verifies that active order execution is strictly locked out in MVP mode."""

    @patch("src.signal_engine.cron_jobs.TradingClient")
    def test_execution_lockout_when_disabled(self, mock_trading_client):
        """When ENABLE_TRADE_EXECUTION is False, no trade must ever be dispatched to Alpaca."""
        with patch("src.signal_engine.cron_jobs.ENABLE_TRADE_EXECUTION", False):
            # Bullish crossover trigger
            execute_signal(current_ema=12.5, previous_ema=5.0, symbol="SPY", qty=1.0)
            mock_trading_client.assert_not_called()

            # Bearish crossover trigger
            execute_signal(current_ema=-15.0, previous_ema=-2.0, symbol="SPY", qty=1.0)
            mock_trading_client.assert_not_called()

    @patch("src.signal_engine.cron_jobs.TradingClient")
    def test_execution_dispatches_when_enabled(self, mock_trading_client):
        """When ENABLE_TRADE_EXECUTION is True, orders are submitted through TradingClient."""
        mock_instance = MagicMock()
        mock_trading_client.return_value = mock_instance

        with patch("src.signal_engine.cron_jobs.ENABLE_TRADE_EXECUTION", True):
            # Bullish crossover: current > previous and current > 0
            execute_signal(current_ema=12.5, previous_ema=5.0, symbol="SPY", qty=1.0)
            self.assertEqual(mock_trading_client.call_count, 1)
            self.assertEqual(mock_instance.submit_order.call_count, 1)

    @patch("src.signal_engine.cron_jobs.TradingClient")
    def test_neutral_stance_no_order_even_if_enabled(self, mock_trading_client):
        """Neutral stances inside deadband must never trigger orders, even if execution is enabled."""
        mock_instance = MagicMock()
        mock_trading_client.return_value = mock_instance

        with patch("src.signal_engine.cron_jobs.ENABLE_TRADE_EXECUTION", True):
            # Neutral case: current <= previous when positive
            execute_signal(current_ema=5.0, previous_ema=8.0, symbol="SPY", qty=1.0)
            mock_trading_client.assert_not_called()
            mock_instance.submit_order.assert_not_called()


if __name__ == "__main__":
    unittest.main()
