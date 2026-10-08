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


def sync_signals_to_ledger(df_signals: pd.DataFrame, ledger_path: Optional[str] = None) -> int:
    """
    Syncs/backfills signals from a DataFrame (e.g. from PostgreSQL event_signals or dashboard memory)
    into the append-only ledger without creating duplicates.
    Returns the number of new records added.
    """
    if df_signals is None or df_signals.empty:
        return 0

    ensure_ledger_initialized(ledger_path)
    path = ledger_path or get_ledger_path()

    existing_keys = set()
    try:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            df_ledger = pd.read_csv(path)
            if not df_ledger.empty and "timestamp" in df_ledger.columns and "index_ticker" in df_ledger.columns:
                for _, row in df_ledger.iterrows():
                    existing_keys.add((str(row["timestamp"]), str(row["index_ticker"])))
    except Exception as e:
        logger.warning(f"Could not read existing ledger for deduplication: {e}")

    df_clean = df_signals.copy()
    if "timestamp" not in df_clean.columns:
        return 0

    df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])
    df_clean = df_clean.sort_values("timestamp").reset_index(drop=True)

    if "sentiment_index" in df_clean.columns:
        raw_series = df_clean["sentiment_index"].astype(float)
    elif "sentiment_score" in df_clean.columns:
        raw_series = df_clean["sentiment_score"].astype(float) * 100.0
    else:
        return 0

    ticker_col = "index_ticker" if "index_ticker" in df_clean.columns else "ticker"
    region_col = "market_region" if "market_region" in df_clean.columns else "region"

    df_clean["_raw_val"] = raw_series
    df_clean["_ema_val"] = df_clean.groupby(ticker_col)["_raw_val"].transform(
        lambda s: s.ewm(span=4, adjust=False).mean()
    )

    new_records = []
    for _, row in df_clean.iterrows():
        ts_str = pd.to_datetime(row["timestamp"]).isoformat()
        ticker = str(row.get(ticker_col, "UNKNOWN"))
        region = str(row.get(region_col, "GLOBAL"))

        if (ts_str, ticker) in existing_keys:
            continue

        raw_val = round(float(row["_raw_val"]), 4)
        ema_val = round(float(row["_ema_val"]), 4)

        if ema_val >= 5.0:
            stance = "BULLISH"
        elif ema_val <= -5.0:
            stance = "BEARISH"
        else:
            stance = "NEUTRAL"

        new_records.append([
            ts_str,
            region,
            ticker,
            raw_val,
            ema_val,
            stance,
            "clm-8b-v1",
            "HEAD"
        ])
        existing_keys.add((ts_str, ticker))

    if new_records:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(new_records)
        logger.info(f"Synced {len(new_records)} historical signals into forward test ledger.")

    return len(new_records)


def load_forward_test_metrics(
    ledger_path: Optional[str] = None,
    df_signals: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Computes summary out-of-sample signal statistics from the public forward evaluation ledger.
    If df_signals is provided, automatically syncs any unrecorded historical signals first.
    """
    ensure_ledger_initialized(ledger_path)
    path = ledger_path or get_ledger_path()

    if df_signals is not None and not df_signals.empty:
        sync_signals_to_ledger(df_signals, ledger_path=path)

    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Error reading forward signal ledger: {e}")
        df = pd.DataFrame()

    if df.empty and df_signals is not None and not df_signals.empty:
        sync_signals_to_ledger(df_signals, ledger_path=path)
        try:
            df = pd.read_csv(path)
        except Exception:
            pass

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
    if "directional_stance" in df.columns:
        directional_mask = df["directional_stance"].astype(str).str.upper().isin(["BULLISH", "BEARISH"])
    else:
        directional_mask = df["ema_sentiment"].abs() >= 5.0

    directional_calls = int(directional_mask.sum())
    neutral_filtered = int((~directional_mask).sum())

    # Directional Hit Rate:
    directional_hit_rate = None
    if "forward_hit" in df.columns and directional_calls > 0:
        valid_hits = df.loc[directional_mask, "forward_hit"].dropna()
        if len(valid_hits) > 0:
            directional_hit_rate = round(float(valid_hits.mean() * 100.0), 2)
    elif directional_calls > 0:
        # Measure directional continuation across consecutive observations
        df_sorted = df.sort_values("timestamp").reset_index(drop=True)
        ticker_col = "index_ticker" if "index_ticker" in df_sorted.columns else "region"
        df_sorted["fwd_raw"] = df_sorted.groupby(ticker_col)["raw_sentiment"].shift(-1)
        valid_eval = df_sorted[df_sorted["fwd_raw"].notna() & directional_mask]
        if len(valid_eval) >= 3:
            hits = (
                (valid_eval["directional_stance"] == "BULLISH") & (valid_eval["fwd_raw"] > 0)
            ) | (
                (valid_eval["directional_stance"] == "BEARISH") & (valid_eval["fwd_raw"] < 0)
            )
            directional_hit_rate = round(float(hits.mean() * 100.0), 1)

    return {
        "status": "ACTIVE_AUDIT",
        "record_count": total_records,
        "directional_calls": directional_calls,
        "neutral_filtered": neutral_filtered,
        "total_days": unique_dates,
        "directional_hit_rate_pct": directional_hit_rate,
        "latest_update": df["timestamp"].iloc[-1] if total_records > 0 else "N/A"
    }
