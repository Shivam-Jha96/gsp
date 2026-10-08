import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from signal_engine.forward_tester import (
    ensure_ledger_initialized,
    record_forward_signal,
    load_forward_test_metrics,
    LEDGER_COLUMNS
)


class TestForwardTester(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        self.temp_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_ensure_ledger_initialized(self):
        ensure_ledger_initialized(ledger_path=self.temp_path)
        self.assertTrue(os.path.exists(self.temp_path))
        with open(self.temp_path, "r", encoding="utf-8") as f:
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
            okf_commit="test_commit",
            ledger_path=self.temp_path
        )
        self.assertEqual(record["region"], "US")
        self.assertEqual(record["index_ticker"], "SPY")
        self.assertEqual(record["target_position"], 1.0)
        self.assertEqual(record["model_version"], "clm-8b-v1")

    def test_load_forward_test_metrics(self):
        # 1. Flat/cash day (target_position=0, daily_pnl=0)
        record_forward_signal(
            region="US",
            index_ticker="SPY",
            raw_sentiment=5.0,
            ema_sentiment=4.0,
            target_position=0.0,
            simulated_price=580.0,
            daily_pnl_pct=0.0,
            ledger_path=self.temp_path
        )
        # 2. Active winning trade
        record_forward_signal(
            region="US",
            index_ticker="SPY",
            raw_sentiment=15.0,
            ema_sentiment=10.0,
            target_position=1.0,
            simulated_price=585.0,
            daily_pnl_pct=0.25,
            ledger_path=self.temp_path
        )
        metrics = load_forward_test_metrics(ledger_path=self.temp_path)
        self.assertEqual(metrics["status"], "ACTIVE_AUDIT")
        self.assertEqual(metrics["record_count"], 2)
        self.assertEqual(metrics["active_trades"], 1)
        self.assertEqual(metrics["win_rate_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
