"""
Public Out-of-Sample Forward Signal Evaluation & Verification Ledger for Valence.

Maintains an immutable, append-only ledger in reports/forward_test_ledger.csv
to build a verifiable public track record of quantitative macroeconomic directional signals,
deadband filtering efficiency, and predictive accuracy.
"""

import os
import csv
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

LEDGER_COLUMNS = [
    "timestamp",
    "region",
    "index_ticker",
    "raw_sentiment",
    "ema_sentiment",
    "directional_stance",
    "model_version",
    "okf_commit"
]

def get_ledger_path() -> str:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    reports_dir = os.path.join(root_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return os.path.join(reports_dir, "forward_test_ledger.csv")


def ensure_ledger_initialized(ledger_path: Optional[str] = None):
    path = ledger_path or get_ledger_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(LEDGER_COLUMNS)
        logger.info(f"Initialized forward signal ledger at {path}")


def record_forward_signal(
    region: str,
    index_ticker: str,
    raw_sentiment: float,
    ema_sentiment: float,
    directional_stance: str = "NEUTRAL",
    model_version: str = "clm-8b-v1",
    okf_commit: str = "HEAD",
    ledger_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Appends a new point-in-time macroeconomic signal to the public forward evaluation ledger.
    """
    ensure_ledger_initialized(ledger_path)
    path = ledger_path or get_ledger_path()

    now_utc = datetime.now(timezone.utc).isoformat()
    record = [
        now_utc,
        region,
        index_ticker,
        round(raw_sentiment, 4),
        round(ema_sentiment, 4),
        directional_stance.upper(),
        model_version,
        okf_commit
    ]

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(record)

    logger.info(f"Recorded forward signal: [{region}] {index_ticker} (EMA: {ema_sentiment:+.2f}, Stance: {directional_stance.upper()})")
    return dict(zip(LEDGER_COLUMNS, record))


def load_forward_test_metrics(ledger_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes summary out-of-sample signal statistics from the public forward evaluation ledger.
    Evaluates macro conviction (directional calls vs neutral deadband filtering).
    """
    ensure_ledger_initialized(ledger_path)
    path = ledger_path or get_ledger_path()
    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Error reading forward signal ledger: {e}")
        return {
            "status": "NO_DATA",
            "record_count": 0,
            "directional_calls": 0,
            "neutral_filtered": 0,
            "total_days": 0,
            "directional_hit_rate_pct": None,
            "latest_update": "N/A"
        }

    if df.empty:
        return {
            "status": "INITIALIZING",
            "record_count": 0,
            "directional_calls": 0,
            "neutral_filtered": 0,
            "total_days": 0,
            "directional_hit_rate_pct": None,
            "latest_update": "Awaiting first live pipeline run"
        }

    total_records = len(df)
    unique_dates = len(pd.to_datetime(df["timestamp"]).dt.date.unique())

    # Categorize macro conviction:
    # Directional Calls: high conviction outside neutral deadband (BULLISH or BEARISH)
    # Neutral Filtered: low conviction within [-5.0, +5.0] deadband
    if "directional_stance" in df.columns:
        directional_mask = df["directional_stance"].str.upper().isin(["BULLISH", "BEARISH"])
    else:
        directional_mask = df["ema_sentiment"].abs() >= 5.0

    directional_calls = int(directional_mask.sum())
    neutral_filtered = int((~directional_mask).sum())

    # Directional Hit Rate (if realized forward moves are present in audit data)
    directional_hit_rate = None
    if "forward_hit" in df.columns and directional_calls > 0:
        valid_hits = df.loc[directional_mask, "forward_hit"].dropna()
        if len(valid_hits) > 0:
            directional_hit_rate = round(float(valid_hits.mean() * 100.0), 2)

    return {
        "status": "ACTIVE_AUDIT",
        "record_count": total_records,
        "directional_calls": directional_calls,
        "neutral_filtered": neutral_filtered,
        "total_days": unique_dates,
        "directional_hit_rate_pct": directional_hit_rate,
        "latest_update": df["timestamp"].iloc[-1] if total_records > 0 else "N/A"
    }
