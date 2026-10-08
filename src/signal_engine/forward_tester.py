"""
Public Out-of-Sample Forward Testing & Verification Ledger for Valence.

Maintains an immutable, append-only ledger in reports/forward_test_ledger.csv
to build a verifiable public track record of signals, paper trade fills, and out-of-sample alpha.
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
    "target_position",
    "simulated_price",
    "slippage_bps",
    "daily_pnl_pct",
    "cumulative_return_pct",
    "model_version",
    "okf_commit"
]

def get_ledger_path() -> str:
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    reports_dir = os.path.join(root_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    return os.path.join(reports_dir, "forward_test_ledger.csv")


def ensure_ledger_initialized():
    path = get_ledger_path()
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(LEDGER_COLUMNS)
        logger.info(f"Initialized forward test ledger at {path}")


def record_forward_signal(
    region: str,
    index_ticker: str,
    raw_sentiment: float,
    ema_sentiment: float,
    target_position: float,
    simulated_price: float,
    slippage_bps: float = 5.0,
    daily_pnl_pct: float = 0.0,
    model_version: str = "clm-8b-v1",
    okf_commit: str = "HEAD"
) -> Dict[str, Any]:
    """
    Appends a new point-in-time signal to the forward test ledger.
    """
    ensure_ledger_initialized()
    path = get_ledger_path()
    
    # Read existing cumulative return if available
    cum_ret = 0.0
    try:
        df = pd.read_csv(path)
        if not df.empty and "cumulative_return_pct" in df.columns:
            last_cum = df["cumulative_return_pct"].dropna().iloc[-1]
            cum_ret = float(last_cum) + daily_pnl_pct
        else:
            cum_ret = daily_pnl_pct
    except Exception:
        cum_ret = daily_pnl_pct

    now_utc = datetime.now(timezone.utc).isoformat()
    record = [
        now_utc,
        region,
        index_ticker,
        round(raw_sentiment, 4),
        round(ema_sentiment, 4),
        round(target_position, 1),
        round(simulated_price, 2),
        round(slippage_bps, 1),
        round(daily_pnl_pct, 4),
        round(cum_ret, 4),
        model_version,
        okf_commit
    ]

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(record)

    logger.info(f"Recorded forward test row: [{region}] {index_ticker} (EMA: {ema_sentiment:+.2f}, Pos: {target_position})")
    return dict(zip(LEDGER_COLUMNS, record))


def load_forward_test_metrics() -> Dict[str, Any]:
    """
    Computes summary out-of-sample forward statistics from the ledger.
    """
    ensure_ledger_initialized()
    path = get_ledger_path()
    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Error reading forward test ledger: {e}")
        return {"status": "NO_DATA", "record_count": 0}

    if df.empty:
        return {
            "status": "INITIALIZING",
            "record_count": 0,
            "total_days": 0,
            "directional_hit_rate_pct": 0.0,
            "realized_sharpe": 0.0,
            "cumulative_return_pct": 0.0
        }

    total_records = len(df)
    unique_dates = len(pd.to_datetime(df["timestamp"]).dt.date.unique())
    cum_ret = float(df["cumulative_return_pct"].iloc[-1]) if "cumulative_return_pct" in df.columns else 0.0
    
    # Calculate win rate if PnL available
    pnls = df["daily_pnl_pct"].dropna() if "daily_pnl_pct" in df.columns else pd.Series()
    win_rate = float((pnls > 0).mean() * 100.0) if len(pnls) > 0 else 0.0
    
    # Realized forward Sharpe
    if len(pnls) >= 5 and pnls.std() > 0:
        realized_sharpe = float((pnls.mean() / pnls.std()) * np.sqrt(252 * 6.5))
    else:
        realized_sharpe = 0.0

    return {
        "status": "ACTIVE_AUDIT",
        "record_count": total_records,
        "total_days": unique_dates,
        "win_rate_pct": round(win_rate, 2),
        "realized_sharpe": round(realized_sharpe, 2),
        "cumulative_return_pct": round(cum_ret, 2),
        "latest_update": df["timestamp"].iloc[-1] if total_records > 0 else "N/A"
    }
