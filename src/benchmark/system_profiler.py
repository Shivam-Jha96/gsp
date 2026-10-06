"""
System, Database & Infrastructure Latency Profiler for Valence.

Profiles:
- PostgreSQL (Supabase) Connection Pool checkout and checkin latency
- Query response times for event_signals (BRIN vs B-Tree)
- Pipeline throughput and simulated UI fragment render times
"""

import time
import os
import sys
import logging
from typing import Dict, Any, List
import numpy as np

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

logger = logging.getLogger(__name__)


class SystemProfiler:
    """
    Profiles database latency, connection pooling, and UI execution performance.
    """
    def __init__(self, db_client=None):
        self.db_client = db_client
        if self.db_client is None:
            try:
                from database.client import get_db_client
                self.db_client = get_db_client()
            except Exception as e:
                logger.info(f"Database client not available for live profiling: {e}")
                self.db_client = None

    def profile_db_connection_pool(self, iterations: int = 10) -> Dict[str, Any]:
        """
        Profiles checkout and return latency for the psycopg2 connection pool.
        """
        if self.db_client is None:
            # Synthetic offline simulation
            mock_latencies = [1.2, 1.4, 0.9, 1.1, 1.3, 1.0, 1.5, 0.8, 1.2, 1.1]
            return {
                "status": "simulated_offline",
                "iterations": iterations,
                "mean_checkout_ms": round(float(np.mean(mock_latencies)), 2),
                "p95_checkout_ms": round(float(np.percentile(mock_latencies, 95)), 2),
                "errors": 0
            }

        latencies = []
        errors = 0
        for _ in range(iterations):
            t0 = time.perf_counter()
            try:
                with self.db_client.get_connection() as conn:
                    # Lightweight keepalive ping
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1;")
                        cur.fetchone()
                lat_ms = (time.perf_counter() - t0) * 1000.0
                latencies.append(lat_ms)
            except Exception as e:
                errors += 1
                logger.warning(f"DB checkout error during benchmark: {e}")

        if not latencies:
            return {"status": "failed", "errors": errors}

        return {
            "status": "live",
            "iterations": iterations,
            "mean_checkout_ms": round(float(np.mean(latencies)), 2),
            "p95_checkout_ms": round(float(np.percentile(latencies, 95)), 2),
            "errors": errors
        }

    def profile_query_performance(self, limit: int = 50) -> Dict[str, Any]:
        """
        Profiles execution time of regional sentiment analytical queries on event_signals.
        """
        if self.db_client is None:
            return {
                "status": "simulated_offline",
                "limit": limit,
                "query_latency_ms": 14.5,
                "row_count": limit
            }

        try:
            t0 = time.perf_counter()
            with self.db_client.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, score, directional_score, market_region, created_at 
                        FROM event_signals 
                        WHERE market_region = 'US' 
                        ORDER BY created_at DESC 
                        LIMIT %s;
                    """, (limit,))
                    rows = cur.fetchall()
            lat_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "status": "live",
                "limit": limit,
                "query_latency_ms": round(lat_ms, 2),
                "row_count": len(rows)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "query_latency_ms": 0.0
            }

    def profile_ui_fragment_simulation(self, iterations: int = 50) -> Dict[str, Any]:
        """
        Simulates the execution of Streamlit @st.fragment data transformation logic.
        """
        import pandas as pd
        dates = pd.date_range("2026-01-01", periods=1000, freq="15min")
        df = pd.DataFrame({
            "score": np.random.uniform(-1, 1, size=len(dates)),
            "directional_score": np.random.uniform(-100, 100, size=len(dates)),
            "region": np.random.choice(["US", "IN", "UK", "JP"], size=len(dates))
        }, index=dates)

        latencies = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            # Simulate filter + EMA calculation + grouping
            filtered = df[df["region"] == "US"]
            ema = filtered["directional_score"].ewm(span=4, adjust=False).mean()
            _ = ema.iloc[-1]
            lat_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(lat_ms)

        return {
            "iterations": iterations,
            "mean_transform_latency_ms": round(float(np.mean(latencies)), 3),
            "p95_transform_latency_ms": round(float(np.percentile(latencies, 95)), 3),
            "p99_transform_latency_ms": round(float(np.percentile(latencies, 99)), 3)
        }
