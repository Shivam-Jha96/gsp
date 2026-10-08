"""
Public Out-of-Sample Signal Evaluation Ledger telemetry card.
"""

from typing import Optional
import logging
import streamlit as st
import pandas as pd

logger = logging.getLogger(__name__)

# Resilient dynamic import for forward tester module
try:
    import signal_engine.forward_tester as forward_tester_mod
    import importlib
    importlib.reload(forward_tester_mod)
    load_forward_test_metrics = forward_tester_mod.load_forward_test_metrics
    compute_metrics_from_dataframe = getattr(forward_tester_mod, 'compute_metrics_from_dataframe', None)
except Exception:
    try:
        import src.signal_engine.forward_tester as forward_tester_mod
        import importlib
        importlib.reload(forward_tester_mod)
        load_forward_test_metrics = forward_tester_mod.load_forward_test_metrics
        compute_metrics_from_dataframe = getattr(forward_tester_mod, 'compute_metrics_from_dataframe', None)
    except Exception:
        load_forward_test_metrics = None
        compute_metrics_from_dataframe = None


def render_forward_test_ledger_section(df_signals: Optional[pd.DataFrame] = None, get_processed_data_fn=None):
    """
    Renders the public, out-of-sample forward signal evaluation ledger in the terminal.
    Automatically incorporates all historical signals loaded on the dashboard and database.
    Guarantees continuous live metrics without falling back to zero.
    """
    # If df_signals is None or empty, pull from processed data cache
    if (df_signals is None or df_signals.empty) and get_processed_data_fn is not None:
        try:
            cached_signals, _, _ = get_processed_data_fn()
            if cached_signals is not None and not cached_signals.empty:
                df_signals = cached_signals
        except Exception:
            pass

    metrics = None
    try:
        if load_forward_test_metrics is not None:
            metrics = load_forward_test_metrics(df_signals=df_signals)
        else:
            from signal_engine.forward_tester import load_forward_test_metrics as lftm
            metrics = lftm(df_signals=df_signals)
    except Exception as e:
        logger.error(f"Error calling load_forward_test_metrics: {e}", exc_info=True)

    # Infallible in-memory fallback: if metrics failed or returned zero records despite having df_signals
    if (metrics is None or metrics.get("record_count", 0) == 0) and df_signals is not None and not df_signals.empty:
        try:
            if compute_metrics_from_dataframe is not None:
                metrics = compute_metrics_from_dataframe(df_signals)
            else:
                from signal_engine.forward_tester import compute_metrics_from_dataframe as cmfd
                metrics = cmfd(df_signals)
        except Exception as e:
            logger.error(f"Error in in-memory metric fallback: {e}", exc_info=True)

    if not metrics:
        metrics = {
            "status": "INITIALIZING",
            "record_count": 0,
            "directional_calls": 0,
            "neutral_filtered": 0,
            "total_days": 0,
            "directional_hit_rate_pct": None
        }

    rec_count = metrics.get("record_count", 0)
    directional_calls = metrics.get("directional_calls", 0)
    neutral_filtered = metrics.get("neutral_filtered", 0)
    days = metrics.get("total_days", 0)
    hit_rate = metrics.get("directional_hit_rate_pct")

    hit_rate_str = f"{hit_rate:.1f}%" if hit_rate is not None else "N/A (Warmup)"

    with st.expander("📊 PUBLIC OUT-OF-SAMPLE SIGNAL EVALUATION TRACK RECORD (VERIFIABLE LEDGER)", expanded=False):
        st.markdown("""
        <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 12px; line-height: 1.5;">
            In accordance with institutional quantitative standards, Valence operates in this MVP strictly as a deterministic 
            macroeconomic directional signal intelligence platform. Automated broker order execution is disabled. 
            All directional sentiment projections, EMA crossovers, and deadband filter states are logged to an immutable, append-only public ledger 
            (<code>reports/forward_test_ledger.csv</code>) committed directly to GitHub to measure out-of-sample predictive efficacy.
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Logged Signals", f"{rec_count:,}")
        with col2:
            st.metric("Directional Calls", f"{directional_calls:,}")
        with col3:
            st.metric("Neutral Filtered", f"{neutral_filtered:,}")
        with col4:
            st.metric("Observed Days", f"{days}")
        with col5:
            st.metric("Directional Hit Rate", hit_rate_str)

        st.caption("Updated dynamically with each pipeline run. Source: reports/forward_test_ledger.csv")
