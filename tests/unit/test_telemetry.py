import unittest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import json

from src.database.telemetry import (
    ensure_pipeline_runs_table,
    track_pipeline_run,
    get_latest_successful_pipeline_run,
    format_pipeline_freshness
)

class MockCursor:
    def __init__(self, db_state):
        self.db_state = db_state
        self.last_query = ""
        self.last_params = ()
        self._results = []

    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params or ()

        if "CREATE TABLE IF NOT EXISTS pipeline_runs" in query:
            self.db_state["table_exists"] = True
            return

        if "INSERT INTO pipeline_runs" in query:
            run_id, pipeline_name, status, started_at, polled, scored, meta = params
            self.db_state["runs"][run_id] = {
                "id": run_id,
                "pipeline_name": pipeline_name,
                "status": status,
                "started_at": started_at,
                "completed_at": None,
                "duration_seconds": None,
                "items_polled": polled,
                "items_scored": scored,
                "metadata": json.loads(meta) if isinstance(meta, str) else meta
            }
            return

        if "UPDATE pipeline_runs" in query:
            if "status = %s" in query and "WHERE id = %s" in query:
                if len(params) == 7:
                    status, completed_at, duration_sec, polled, scored, meta, run_id = params
                    if run_id in self.db_state["runs"]:
                        self.db_state["runs"][run_id].update({
                            "status": status,
                            "completed_at": completed_at,
                            "duration_seconds": duration_sec,
                            "items_polled": polled,
                            "items_scored": scored,
                            "metadata": json.loads(meta) if isinstance(meta, str) else meta
                        })
                elif len(params) == 5:
                    status, completed_at, duration_sec, meta, run_id = params
                    if run_id in self.db_state["runs"]:
                        self.db_state["runs"][run_id].update({
                            "status": status,
                            "completed_at": completed_at,
                            "duration_seconds": duration_sec,
                            "metadata": json.loads(meta) if isinstance(meta, str) else meta
                        })
            return

        if "SELECT id, completed_at, duration_seconds" in query:
            pipeline_name = params[0]
            success_runs = [
                r for r in self.db_state["runs"].values()
                if r["pipeline_name"] == pipeline_name and r["status"] == "SUCCESS" and r["completed_at"] is not None
            ]
            success_runs.sort(key=lambda x: x["completed_at"], reverse=True)
            if success_runs:
                latest = success_runs[0]
                self._results = [(
                    latest["id"],
                    latest["completed_at"],
                    latest["duration_seconds"],
                    latest["items_polled"],
                    latest["items_scored"],
                    latest["metadata"]
                )]
            else:
                self._results = []
            return

    def fetchone(self):
        return self._results[0] if self._results else None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class MockConnection:
    def __init__(self, db_state):
        self.db_state = db_state

    def cursor(self):
        return MockCursor(self.db_state)

    def commit(self):
        pass

    def rollback(self):
        pass


class MockDBClient:
    def __init__(self):
        self.db_state = {"table_exists": False, "runs": {}}

    class _Context:
        def __init__(self, client):
            self.client = client

        def __enter__(self):
            return MockConnection(self.client.db_state)

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def get_connection(self):
        return self._Context(self)


class TestDatabaseTelemetry(unittest.TestCase):
    def setUp(self):
        self.db_client = MockDBClient()

    def test_ensure_pipeline_runs_table(self):
        with self.db_client.get_connection() as conn:
            created = ensure_pipeline_runs_table(conn)
        self.assertTrue(created)
        self.assertTrue(self.db_client.db_state["table_exists"])

    def test_track_pipeline_run_success(self):
        with track_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client) as tracker:
            tracker.record_counts(items_polled=14, items_scored=4)
            tracker.add_metadata("note", "cron trigger")

        latest = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["items_polled"], 14)
        self.assertEqual(latest["items_scored"], 4)
        self.assertEqual(latest["metadata"]["note"], "cron trigger")
        self.assertIsNotNone(latest["completed_at"])

    def test_track_pipeline_run_failure_preserves_last_successful_run(self):
        # Initial success
        with track_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client) as tracker:
            tracker.record_counts(items_polled=14, items_scored=2)

        first_success = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client)

        # Subsequent failure
        with self.assertRaises(ZeroDivisionError):
            with track_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client) as tracker:
                _ = 1 / 0

        after_fail = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client)
        self.assertEqual(after_fail["id"], first_success["id"])

    def test_zero_scored_run_advances_timestamp(self):
        with track_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client) as tracker:
            tracker.record_counts(items_polled=14, items_scored=0)
            tracker.add_metadata("dedup", "all_cached")

        latest = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["items_scored"], 0)

    def test_format_freshness_edge_cases(self):
        fixed_now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

        # Under 1 minute -> just now
        t_recent = fixed_now - timedelta(seconds=20)
        disp, rel, tip, tier = format_pipeline_freshness(t_recent, now_utc=fixed_now)
        self.assertEqual(rel, "just now")
        self.assertEqual(tier, "fresh")

        # 15 minutes ago
        t_15m = fixed_now - timedelta(minutes=15)
        disp, rel, tip, tier = format_pipeline_freshness(t_15m, now_utc=fixed_now)
        self.assertEqual(rel, "15m ago")
        self.assertEqual(tier, "fresh")

        # 3 hours ago -> aging
        t_3h = fixed_now - timedelta(hours=3)
        disp, rel, tip, tier = format_pipeline_freshness(t_3h, now_utc=fixed_now)
        self.assertEqual(rel, "3h ago")
        self.assertEqual(tier, "aging")

        # 6 hours ago -> stale
        t_6h = fixed_now - timedelta(hours=6)
        disp, rel, tip, tier = format_pipeline_freshness(t_6h, now_utc=fixed_now)
        self.assertEqual(rel, "6h ago")
        self.assertEqual(tier, "stale")

        # Fallback to signal timestamp
        t_signal = fixed_now - timedelta(hours=7)
        disp, rel, tip, tier = format_pipeline_freshness(None, fallback_ts=t_signal, now_utc=fixed_now)
        self.assertIn("IST", disp)
        self.assertIn("Latest Signal Timestamp", tip)

        # Live fallback
        disp, rel, tip, tier = format_pipeline_freshness(None, fallback_ts=None, now_utc=fixed_now)
        self.assertEqual(disp, "LIVE")
        self.assertEqual(rel, "live stream")

    def test_format_freshness_dynamic_timezones(self):
        fixed_now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
        # Test UTC
        disp_utc, _, _, _ = format_pipeline_freshness(fixed_now, now_utc=fixed_now, target_tz_str="UTC")
        self.assertIn("UTC", disp_utc)
        self.assertEqual(disp_utc, "12:00 UTC")

        # Test New York (EDT)
        disp_ny, _, _, _ = format_pipeline_freshness(fixed_now, now_utc=fixed_now, target_tz_str="America/New_York")
        self.assertTrue("EDT" in disp_ny or "EST" in disp_ny, f"Expected EDT/EST in {disp_ny}")

        # Test London (BST)
        disp_lon, _, _, _ = format_pipeline_freshness(fixed_now, now_utc=fixed_now, target_tz_str="Europe/London")
        self.assertTrue("BST" in disp_lon or "GMT" in disp_lon, f"Expected BST/GMT in {disp_lon}")

        # Test Tokyo (JST)
        disp_tok, _, _, _ = format_pipeline_freshness(fixed_now, now_utc=fixed_now, target_tz_str="Asia/Tokyo")
        self.assertIn("JST", disp_tok)

        # Test explicit tz_abbr overrides (e.g. from UI selectbox options)
        disp_est, _, _, _ = format_pipeline_freshness(fixed_now, now_utc=fixed_now, target_tz_str="America/New_York", tz_abbr="EST")
        self.assertIn("EST", disp_est)

        disp_gmt, _, _, _ = format_pipeline_freshness(fixed_now, now_utc=fixed_now, target_tz_str="Europe/London", tz_abbr="GMT")
        self.assertIn("GMT", disp_gmt)


if __name__ == "__main__":
    unittest.main()
