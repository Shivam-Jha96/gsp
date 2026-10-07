"""
Telemetry module for tracking and querying Global Macro-Sentiment Pipeline runs.
Supports PostgreSQL (Supabase) via psycopg2 connection pool, with automatic schema
creation, execution timing, fail-safe error isolation, and timezone-aware formatting.
"""

import os
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from contextlib import contextmanager

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo

logger = logging.getLogger(__name__)

PIPELINE_RUNS_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    duration_seconds NUMERIC(10, 2),
    items_polled INT DEFAULT 0,
    items_scored INT DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_lookup 
ON pipeline_runs (pipeline_name, status, completed_at DESC);
"""

class PipelineRunTracker:
    """Helper object passed into track_pipeline_run context to record runtime metrics."""
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.items_polled = 0
        self.items_scored = 0
        self.metadata = {}

    def record_counts(self, items_polled: int = 0, items_scored: int = 0):
        self.items_polled = items_polled
        self.items_scored = items_scored

    def add_metadata(self, key: str, value: Any):
        self.metadata[key] = value


def ensure_pipeline_runs_table(conn) -> bool:
    """Ensures pipeline_runs table and index exist. Fails safely without raising."""
    try:
        with conn.cursor() as cur:
            cur.execute(PIPELINE_RUNS_TABLE_DDL)
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"Could not verify/create pipeline_runs table: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False


@contextmanager
def track_pipeline_run(pipeline_name: str = "macro_sentiment_pipeline", db_client=None):
    """
    Context manager wrapping pipeline execution.
    - Records start timestamp and RUNNING status.
    - On success: records completed_at, duration_seconds, counts, and SUCCESS status.
    - On exception: records completed_at, FAILED status, error details, and re-raises.
    - Fail-safe: if DB client is missing or fails, logs warning and yields without crashing.
    """
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    tracker = PipelineRunTracker(run_id)

    # 1. Record START if DB available
    if db_client:
        try:
            with db_client.get_connection() as conn:
                ensure_pipeline_runs_table(conn)
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO pipeline_runs (id, pipeline_name, status, started_at, items_polled, items_scored, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (run_id, pipeline_name, "RUNNING", started_at, 0, 0, "{}"))
                conn.commit()
        except Exception as e:
            logger.warning(f"[TELEMETRY] Failed to record run start for {run_id}: {e}")

    try:
        yield tracker
        # Execution succeeded
        completed_at = datetime.now(timezone.utc)
        duration_sec = round((completed_at - started_at).total_seconds(), 2)

        if db_client:
            try:
                with db_client.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE pipeline_runs
                            SET status = %s,
                                completed_at = %s,
                                duration_seconds = %s,
                                items_polled = %s,
                                items_scored = %s,
                                metadata = %s
                            WHERE id = %s;
                        """, (
                            "SUCCESS",
                            completed_at,
                            duration_sec,
                            tracker.items_polled,
                            tracker.items_scored,
                            json.dumps(tracker.metadata),
                            run_id
                        ))
                    conn.commit()
                logger.info(f"[TELEMETRY] Pipeline run {run_id} recorded SUCCESS ({duration_sec}s, {tracker.items_scored} scored).")
            except Exception as e:
                logger.warning(f"[TELEMETRY] Failed to record run success for {run_id}: {e}")

    except Exception as exc:
        completed_at = datetime.now(timezone.utc)
        duration_sec = round((completed_at - started_at).total_seconds(), 2)
        tracker.add_metadata("error", str(exc))

        if db_client:
            try:
                with db_client.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE pipeline_runs
                            SET status = %s,
                                completed_at = %s,
                                duration_seconds = %s,
                                metadata = %s
                            WHERE id = %s;
                        """, ("FAILED", completed_at, duration_sec, json.dumps(tracker.metadata), run_id))
                    conn.commit()
                logger.warning(f"[TELEMETRY] Pipeline run {run_id} recorded FAILED after {duration_sec}s: {exc}")
            except Exception as e:
                logger.warning(f"[TELEMETRY] Failed to record run failure for {run_id}: {e}")
        raise exc


def get_latest_successful_pipeline_run(pipeline_name: str = "macro_sentiment_pipeline", db_client=None) -> Optional[Dict[str, Any]]:
    """
    Queries the most recent successful run of the given pipeline.
    Returns dict with keys: id, completed_at, duration_seconds, items_polled, items_scored, metadata.
    Returns None if no successful run exists or on DB error.
    """
    if not db_client:
        return None

    try:
        with db_client.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, completed_at, duration_seconds, items_polled, items_scored, metadata
                    FROM pipeline_runs
                    WHERE pipeline_name = %s AND status = 'SUCCESS' AND completed_at IS NOT NULL
                    ORDER BY completed_at DESC
                    LIMIT 1;
                """, (pipeline_name,))
                row = cur.fetchone()
                if row:
                    return {
                        "id": str(row[0]),
                        "completed_at": row[1],
                        "duration_seconds": float(row[2]) if row[2] is not None else None,
                        "items_polled": row[3],
                        "items_scored": row[4],
                        "metadata": row[5] or {}
                    }
    except Exception as e:
        logger.warning(f"[TELEMETRY] Failed to fetch latest successful pipeline run: {e}")
    return None


def format_pipeline_freshness(
    completed_at: Optional[datetime],
    fallback_ts: Optional[datetime] = None,
    now_utc: Optional[datetime] = None,
    target_tz_str: str = "Asia/Kolkata"
) -> Tuple[str, str, str, str]:
    """
    Formats the freshness badge strings:
    Returns (time_display_str, relative_str, tooltip_str, freshness_tier)
    - time_display_str: e.g. "13:30 IST"
    - relative_str: e.g. "5m ago", "just now", "2h ago"
    - tooltip_str: Detailed inspection string for HTML title attribute
    - freshness_tier: "fresh" (< 2h15m), "aging" (2h15m - 4h), "stale" (> 4h)
    """
    target_dt = completed_at if completed_at is not None else fallback_ts
    if target_dt is None:
        return "LIVE", "live stream", "No pipeline completion records found; streaming live updates", "fresh"

    # Normalize timezone
    if target_dt.tzinfo is None:
        target_dt = target_dt.replace(tzinfo=timezone.utc)

    now = now_utc if now_utc is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # Convert to target timezone for display
    try:
        tz = ZoneInfo(target_tz_str)
        local_dt = target_dt.astimezone(tz)
    except Exception:
        local_dt = target_dt
        target_tz_str = "UTC"

    # Compute elapsed seconds
    elapsed_seconds = max(0, int((now - target_dt).total_seconds()))
    minutes = elapsed_seconds // 60
    hours = minutes // 60
    days = hours // 24

    if elapsed_seconds < 60:
        relative_str = "just now"
    elif minutes < 60:
        relative_str = f"{minutes}m ago"
    elif hours < 24:
        relative_str = f"{hours}h {minutes % 60}m ago" if minutes % 60 > 0 else f"{hours}h ago"
    else:
        relative_str = f"{days}d ago"

    # Time display formatting with dynamic timezone abbreviation
    try:
        tz = ZoneInfo(target_tz_str)
        local_dt = target_dt.astimezone(tz)
        now_local = now.astimezone(tz)
    except Exception:
        local_dt = target_dt
        now_local = now
        target_tz_str = "UTC"

    tz_abbr = local_dt.strftime("%Z")
    if not tz_abbr or tz_abbr.startswith(("+", "-")):
        tz_abbr = target_tz_str.split("/")[-1].replace("_", " ")

    try:
        if local_dt.date() == now_local.date():
            time_display_str = local_dt.strftime(f"%H:%M {tz_abbr}")
        else:
            time_display_str = local_dt.strftime(f"%d %b %H:%M {tz_abbr}")
    except Exception:
        time_display_str = local_dt.strftime(f"%H:%M {tz_abbr}")

    # Determine freshness tier (since pipeline runs every 2 hours)
    if minutes <= 135:  # 2h 15m
        freshness_tier = "fresh"
    elif minutes <= 240: # 4h
        freshness_tier = "aging"
    else:
        freshness_tier = "stale"

    source_label = "Pipeline Run" if completed_at is not None else "Latest Signal Timestamp"
    iso_str = local_dt.strftime("%Y-%m-%d %H:%M:%S")
    tooltip_str = f"{source_label} completed at {iso_str} {target_tz_str} ({relative_str})"

    return time_display_str, relative_str, tooltip_str, freshness_tier
