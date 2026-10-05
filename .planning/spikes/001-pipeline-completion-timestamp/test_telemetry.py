import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import json

from spike_telemetry import (
    ensure_pipeline_runs_table,
    track_pipeline_run,
    get_latest_successful_pipeline_run,
    format_pipeline_freshness,
    PIPELINE_RUNS_TABLE_DDL
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

        # Simulate Table Creation
        if "CREATE TABLE IF NOT EXISTS pipeline_runs" in query:
            self.db_state["table_exists"] = True
            return

        # Simulate Insert
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

        # Simulate Update
        if "UPDATE pipeline_runs" in query:
            if "status = %s" in query and "WHERE id = %s" in query:
                # Can be success update (7 params) or failed update (5 params)
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

        # Simulate Select latest success
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
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return MockCursor(self.db_state)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


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


class TestPipelineTelemetry(unittest.TestCase):
    def setUp(self):
        self.db_client = MockDBClient()

    def test_ensure_table_creates_schema(self):
        with self.db_client.get_connection() as conn:
            success = ensure_pipeline_runs_table(conn)
        self.assertTrue(success)
        self.assertTrue(self.db_client.db_state["table_exists"])

    def test_track_pipeline_run_success(self):
        with track_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client) as tracker:
            tracker.record_counts(items_polled=20, items_scored=5)
            tracker.add_metadata("regions", ["IN", "US", "UK", "JP"])

        latest = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["items_polled"], 20)
        self.assertEqual(latest["items_scored"], 5)
        self.assertEqual(latest["metadata"]["regions"], ["IN", "US", "UK", "JP"])
        self.assertIsNotNone(latest["completed_at"])
        self.assertGreaterEqual(latest["duration_seconds"], 0.0)

    def test_track_pipeline_run_failure_does_not_mask_previous_success(self):
        # 1. First run succeeds
        with track_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client) as tracker:
            tracker.record_counts(items_polled=15, items_scored=3)

        first_success = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client)
        self.assertIsNotNone(first_success)

        # 2. Second run crashes
        with self.assertRaises(RuntimeError):
            with track_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client) as tracker:
                raise RuntimeError("API timeout during scoring")

        # 3. Latest successful run must STILL point to first_success, NOT the failed run
        latest_after_failure = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client)
        self.assertEqual(latest_after_failure["id"], first_success["id"])
        self.assertEqual(latest_after_failure["items_scored"], 3)

    def test_zero_payload_run_records_success(self):
        # Even if 0 items scored (zero-opex dedup), pipeline completed successfully
        with track_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client) as tracker:
            tracker.record_counts(items_polled=14, items_scored=0)
            tracker.add_metadata("dedup_status", "all_cached")

        latest = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=self.db_client)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["items_scored"], 0)
        self.assertEqual(latest["metadata"]["dedup_status"], "all_cached")

    def test_format_freshness_scenarios(self):
        fixed_now = datetime(2026, 10, 5, 14, 0, 0, tzinfo=timezone.utc)

        # Case 1: Run completed 5 minutes ago
        run_5m_ago = fixed_now - timedelta(minutes=5)
        disp, rel, tip, tier = format_pipeline_freshness(run_5m_ago, now_utc=fixed_now)
        # 14:00 UTC = 19:30 IST; 5m ago = 19:25 IST
        self.assertEqual(disp, "19:25 IST")
        self.assertEqual(rel, "5m ago")
        self.assertEqual(tier, "fresh")
        self.assertIn("Pipeline Run completed at", tip)

        # Case 2: Run completed 30 seconds ago
        run_just_now = fixed_now - timedelta(seconds=30)
        disp, rel, tip, tier = format_pipeline_freshness(run_just_now, now_utc=fixed_now)
        self.assertEqual(rel, "just now")
        self.assertEqual(tier, "fresh")

        # Case 3: Run completed 3 hours ago (pipeline runs every 2h -> aging)
        run_3h_ago = fixed_now - timedelta(hours=3)
        disp, rel, tip, tier = format_pipeline_freshness(run_3h_ago, now_utc=fixed_now)
        self.assertEqual(rel, "3h ago")
        self.assertEqual(tier, "aging")

        # Case 4: Run completed 5 hours ago (stale)
        run_5h_ago = fixed_now - timedelta(hours=5)
        disp, rel, tip, tier = format_pipeline_freshness(run_5h_ago, now_utc=fixed_now)
        self.assertEqual(rel, "5h ago")
        self.assertEqual(tier, "stale")

        # Case 5: No pipeline runs exist yet, fallback to RSS news item timestamp
        rss_ts = fixed_now - timedelta(hours=8, minutes=29)
        disp, rel, tip, tier = format_pipeline_freshness(None, fallback_ts=rss_ts, now_utc=fixed_now)
        self.assertIn("IST", disp)
        self.assertIn("Latest Signal Timestamp", tip)

        # Case 6: Completely empty DB
        disp, rel, tip, tier = format_pipeline_freshness(None, fallback_ts=None, now_utc=fixed_now)
        self.assertEqual(disp, "LIVE")
        self.assertEqual(rel, "live stream")


if __name__ == "__main__":
    unittest.main()
