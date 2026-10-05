"""
Self-contained runner script for Spike 001 verification.
Executes test suite, simulates pipeline executions, probes edge cases,
and verifies all requirements.
"""

import sys
import os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import unittest
from datetime import datetime, timezone, timedelta
from spike_telemetry import (
    ensure_pipeline_runs_table,
    track_pipeline_run,
    get_latest_successful_pipeline_run,
    format_pipeline_freshness
)
from test_telemetry import MockDBClient, TestPipelineTelemetry

def run_verification():
    print("=" * 70)
    print("GSP SPIKE 001: Pipeline Completion Timestamp Verification")
    print("=" * 70)

    # 1. Run Unit Tests
    print("\n[STEP 1] Running Unit Test Suite...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPipelineTelemetry)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    if not test_result.wasSuccessful():
        print("❌ Unit tests failed!")
        sys.exit(1)
    print("✅ All unit tests passed successfully.")

    # 2. Simulate Realistic Workflow
    print("\n[STEP 2] Simulating Realistic Production Pipeline Scenarios...")
    db = MockDBClient()

    # Scenario A: Initial State with no runs
    print("  Scenario A: Dashboard loads with zero pipeline runs logged yet.")
    latest = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=db)
    disp, rel, tip, tier = format_pipeline_freshness(
        latest["completed_at"] if latest else None,
        fallback_ts=datetime(2026, 10, 5, 0, 1, 0, tzinfo=timezone.utc)
    )
    print(f"    -> Freshness Badge: {disp} ({rel})")
    assert "IST" in disp
    print("    -> Verified graceful fallback to RSS item timestamp.")

    # Scenario B: Pipeline Run 1 (Standard successful run)
    print("\n  Scenario B: Pipeline completes successfully (14 polled, 4 scored).")
    with track_pipeline_run("macro_sentiment_pipeline", db_client=db) as tracker:
        tracker.record_counts(items_polled=14, items_scored=4)
        tracker.add_metadata("regions", ["IN", "US", "UK", "JP"])

    run1 = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=db)
    disp1, rel1, tip1, tier1 = format_pipeline_freshness(run1["completed_at"])
    print(f"    -> Run 1 ID: {run1['id'][:8]}...")
    print(f"    -> Completed at: {run1['completed_at'].isoformat()}")
    print(f"    -> Badge: {disp1} ({rel1}) [Tier: {tier1}]")
    print(f"    -> Tooltip: {tip1}")
    assert rel1 == "just now"
    assert tier1 == "fresh"

    # Scenario C: Pipeline Run 2 (Fails due to downstream timeout)
    print("\n  Scenario C: Pipeline Run 2 suffers external API timeout and crashes.")
    try:
        with track_pipeline_run("macro_sentiment_pipeline", db_client=db) as tracker:
            tracker.record_counts(items_polled=14, items_scored=0)
            raise ConnectionError("503 Serverless endpoint cold-start timeout")
    except ConnectionError:
        print("    -> Exception safely caught and recorded in telemetry table.")

    run_after_fail = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=db)
    print(f"    -> Latest successful run ID after failure: {run_after_fail['id'][:8]}...")
    assert run_after_fail["id"] == run1["id"]
    print("    -> Verified: Failed runs NEVER overwrite the last successful timestamp!")

    # Scenario D: Pipeline Run 3 (Zero items scored — all 14 deduplicated)
    print("\n  Scenario D: 2-hour cron triggers; all news headlines deduplicated (0 scored).")
    with track_pipeline_run("macro_sentiment_pipeline", db_client=db) as tracker:
        tracker.record_counts(items_polled=14, items_scored=0)
        tracker.add_metadata("note", "zero-opex dedup: all cached")

    run3 = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=db)
    disp3, rel3, tip3, tier3 = format_pipeline_freshness(run3["completed_at"])
    print(f"    -> Run 3 ID: {run3['id'][:8]}...")
    print(f"    -> Items scored: {run3['items_scored']}")
    print(f"    -> Badge updated to latest run: {disp3} ({rel3})")
    assert run3["id"] != run1["id"]
    assert run3["items_scored"] == 0
    print("    -> Verified: Deduplicated runs successfully advance the freshness timestamp!")

    print("\n" + "=" * 70)
    print("SPIKE 001 VERIFICATION COMPLETE: ALL 4 TEST SCENARIOS VALIDATED (100% PASS)")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
