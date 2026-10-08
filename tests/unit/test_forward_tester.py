"""
Unit tests for Valence Public Forward Testing Engine & Ledger.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from signal_engine.forward_tester import (
    ensure_ledger_initialized,
    record_forward_signal,
    load_forward_test_metrics,
    get_ledger_path,
    LEDGER_COLUMNS
)


class TestForwardTester(unittest.TestCase):
    def test_ensure_ledger_initialized(self):
        ensure_ledger_initialized()
        path = get_ledger_path()
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            header = f.readline().strip().split(",")
        self.assertEqual(header, LEDGER_COLUMNS)

    def test_record_forward_signal(self):
        record = record_forward_signal(
            region="US",
            index_ticker="SPY",
            raw_sentiment=12.5,
            ema_sentiment=8.2,
            target_position=1.0,
            simulated_price=580.25,
            daily_pnl_pct=0.15,
            model_version="clm-8b-v1",
            okf_commit="test_commit"
        )
        self.assertEqual(record["region"], "US")
        self.assertEqual(record["index_ticker"], "SPY")
        self.assertEqual(record["target_position"], 1.0)
        self.assertEqual(record["model_version"], "clm-8b-v1")

    def test_load_forward_test_metrics(self):
        record_forward_signal(
            region="US",
            index_ticker="SPY",
            raw_sentiment=5.0,
            ema_sentiment=4.0,
            target_position=0.0,
            simulated_price=580.0
        )
        metrics = load_forward_test_metrics()
        self.assertIn("status", metrics)
        self.assertIn("record_count", metrics)
        self.assertGreaterEqual(metrics["record_count"], 1)


if __name__ == "__main__":
    unittest.main()
