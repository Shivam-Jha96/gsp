"""
Valence: Institutional Macroeconomic Sentiment & Directional Signal Engine.
Clean, reactive Streamlit dashboard orchestrator.
"""

import os
import sys
import time
import logging
import streamlit as st
import pandas as pd

logger = logging.getLogger(__name__)

# Configure paths to ensure absolute resolution across Streamlit Cloud runtimes
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
root_dir = os.path.abspath(os.path.join(src_dir, '..'))

for p in [src_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Bridge Streamlit Cloud secrets to environment variables if not already present
if "DATABASE_URL" not in os.environ:
    try:
        if hasattr(st, "secrets"):
            if "DATABASE_URL" in st.secrets:
                os.environ["DATABASE_URL"] = str(st.secrets["DATABASE_URL"])
            elif "postgres" in st.secrets and "DATABASE_URL" in st.secrets["postgres"]:
                os.environ["DATABASE_URL"] = str(st.secrets["postgres"]["DATABASE_URL"])
            elif "supabase" in st.secrets and "DATABASE_URL" in st.secrets["supabase"]:
                os.environ["DATABASE_URL"] = str(st.secrets["supabase"]["DATABASE_URL"])
    except Exception:
        pass

# Dynamic resilient database imports
try:
    import database.client as db_client_mod
    if not hasattr(db_client_mod, 'reset_db_client'):
        import importlib
        importlib.reload(db_client_mod)
    get_db_client = db_client_mod.get_db_client
    reset_db_client = getattr(db_client_mod, 'reset_db_client', None)
except Exception:
    import src.database.client as db_client_mod
    if not hasattr(db_client_mod, 'reset_db_client'):
        import importlib
        importlib.reload(db_client_mod)
    get_db_client = db_client_mod.get_db_client
    reset_db_client = getattr(db_client_mod, 'reset_db_client', None)

try:
    import database.telemetry as db_telemetry_mod
    import importlib
    importlib.reload(db_telemetry_mod)
    get_latest_successful_pipeline_run = db_telemetry_mod.get_latest_successful_pipeline_run
except Exception:
    import src.database.telemetry as db_telemetry_mod
    import importlib
    importlib.reload(db_telemetry_mod)
    get_latest_successful_pipeline_run = db_telemetry_mod.get_latest_successful_pipeline_run

# State persistence
try:
    import ui.state_persistence as state_persistence_mod
    init_session_persistence = state_persistence_mod.init_session_persistence
    render_local_storage_sync_script = state_persistence_mod.render_local_storage_sync_script
except Exception:
    import src.ui.state_persistence as state_persistence_mod
    init_session_persistence = state_persistence_mod.init_session_persistence
    render_local_storage_sync_script = state_persistence_mod.render_local_storage_sync_script

# UI Styling & Modular Components
import importlib
try:
    import ui.styles as ui_styles_mod
    import ui.components as ui_components_mod
    import ui.components.ledger as ui_ledger_mod
    import ui.components.header as ui_header_mod
    importlib.reload(ui_styles_mod)
    importlib.reload(ui_components_mod)
    importlib.reload(ui_ledger_mod)
    importlib.reload(ui_header_mod)
    from ui.styles import inject_global_styles
    from ui.components import (
        make_fragment_decorator,
        render_header_banner,
        render_usp_banner,
        render_filter_toolbar,
        render_analytics_surface,
        render_live_intelligence_feed,
        render_forward_test_ledger_section,
        render_regulatory_disclaimer,
    )
except Exception:
    import src.ui.styles as ui_styles_mod
    import src.ui.components as ui_components_mod
    import src.ui.components.ledger as ui_ledger_mod
    import src.ui.components.header as ui_header_mod
    importlib.reload(ui_styles_mod)
    importlib.reload(ui_components_mod)
    importlib.reload(ui_ledger_mod)
    importlib.reload(ui_header_mod)
    from src.ui.styles import inject_global_styles
    from src.ui.components import (
        make_fragment_decorator,
        render_header_banner,
        render_usp_banner,
        render_filter_toolbar,
        render_analytics_surface,
        render_live_intelligence_feed,
        render_forward_test_ledger_section,
        render_regulatory_disclaimer,
    )

# Page configuration & branding
valence_favicon_path = os.path.join(current_dir, "assets", "valence_logo_flat.svg")
st.set_page_config(
    page_title="Valence",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon=valence_favicon_path if os.path.exists(valence_favicon_path) else "📈"
)

# Inject master permanent dark theme styles
inject_global_styles(is_dark=True)


# --- Data Access & Processing Layer ---

@st.cache_data(ttl=300)
def load_data():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        now = pd.Timestamp.now('UTC')
        dates = pd.date_range(end=now, periods=100, freq='10min')
        import numpy as np
        np.random.seed(42)
        scores = np.random.uniform(-1, 1, size=len(dates))
        mock_signals = pd.DataFrame({
            "timestamp": dates,
            "market_region": np.random.choice(["US", "UK", "IN", "JP"], size=len(dates)),
            "sentiment_score": scores
        })
        mock_signals['index_ticker'] = np.random.choice(["S&P 500", "NASDAQ", "Nifty 50"], size=len(dates))
        mock_payloads = pd.DataFrame({
            "timestamp": dates,
            "market_region": mock_signals['market_region'].values,
            "index_ticker": mock_signals['index_ticker'].values,
            "sentiment_score": mock_signals['sentiment_score'].values,
            "raw_text": ["Market opening shows mixed signals..."] * len(dates)
        })
        return mock_signals, mock_payloads, None

    max_retries = 2
    for attempt in range(max_retries):
        try:
            client = get_db_client()
            with client.get_connection() as conn:
                query_signals = "SELECT id, timestamp, market_region, index_ticker, sentiment_score FROM event_signals ORDER BY timestamp DESC LIMIT 2000"
                df_signals = pd.read_sql(query_signals, conn)
                df_signals['timestamp'] = pd.to_datetime(df_signals['timestamp'])

                query_payloads = """
                    SELECT s.id, s.timestamp, s.market_region, s.index_ticker, s.sentiment_score, p.raw_text
                    FROM event_signals s JOIN event_payloads p ON s.id = p.id
                    ORDER BY s.timestamp DESC LIMIT 2000
                """
                df_payloads = pd.read_sql(query_payloads, conn)
                df_payloads['timestamp'] = pd.to_datetime(df_payloads['timestamp'])

            latest_run = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=client)
            return df_signals, df_payloads, latest_run
        except Exception as e:
            if attempt < max_retries - 1:
                if reset_db_client:
                    reset_db_client()
                else:
                    try:
                        client = get_db_client()
                        client.close_pool()
                    except Exception:
                        pass
                time.sleep(0.5)
                continue
            else:
                logger.warning(f"Database query failed, serving mock data: {e}")
                now = pd.Timestamp.now('UTC')
                dates = pd.date_range(end=now, periods=100, freq='10min')
                import numpy as np
                np.random.seed(42)
                scores = np.random.uniform(-1, 1, size=len(dates))
                mock_signals = pd.DataFrame({
                    "timestamp": dates,
                    "market_region": np.random.choice(["US", "UK", "IN", "JP"], size=len(dates)),
                    "sentiment_score": scores
                })
                mock_signals['index_ticker'] = np.random.choice(["S&P 500", "NASDAQ", "Nifty 50"], size=len(dates))
                mock_payloads = pd.DataFrame({
                    "timestamp": dates,
                    "market_region": mock_signals['market_region'].values,
                    "index_ticker": mock_signals['index_ticker'].values,
                    "sentiment_score": mock_signals['sentiment_score'].values,
                    "raw_text": ["Market opening shows mixed signals..."] * len(dates)
                })
                return mock_signals, mock_payloads, None


@st.cache_data(ttl=300)
def get_processed_data():
    df_signals, df_payloads, latest_pipeline_run = load_data()
    if df_signals.empty and df_payloads.empty:
        return df_signals, df_payloads, latest_pipeline_run

    # Real-time regional relevance and contaminant gatekeeper:
    if os.environ.get("DATABASE_URL") and not df_payloads.empty and 'raw_text' in df_payloads.columns and 'id' in df_payloads.columns:
        try:
            from ingestion.classifier import RegionalAffinityClassifier
            classifier = RegionalAffinityClassifier()
            valid_ids = set()
            for _, row in df_payloads.iterrows():
                res = classifier.classify_and_validate(
                    headline=str(row.get('raw_text', '')),
                    summary="",
                    expected_region=str(row.get('market_region', '')),
                    expected_ticker=str(row.get('index_ticker', '')),
                    allow_reroute=False
                )
                if res is not None:
                    valid_ids.add(row['id'])

            if valid_ids:
                df_payloads = df_payloads[df_payloads['id'].isin(valid_ids)].copy()
                if 'id' in df_signals.columns:
                    df_signals = df_signals[df_signals['id'].isin(valid_ids)].copy()
        except Exception:
            pass

    # Real-time deduplication gatekeeper:
    if not df_payloads.empty and 'raw_text' in df_payloads.columns and 'id' in df_payloads.columns:
        try:
            from ingestion.dedup import canonical_fingerprint
            seen_fps = set()
            unique_ids = set()
            df_sorted = df_payloads.sort_values('timestamp', ascending=False)
            for _, row in df_sorted.iterrows():
                fp = canonical_fingerprint(str(row.get('raw_text', '')))
                if fp and fp not in seen_fps:
                    seen_fps.add(fp)
                    unique_ids.add(row['id'])

            if unique_ids:
                df_payloads = df_payloads[df_payloads['id'].isin(unique_ids)].copy()
                if 'id' in df_signals.columns:
                    df_signals = df_signals[df_signals['id'].isin(unique_ids)].copy()
        except Exception:
            pass

    # Enforce strict cutoff floor: 12:00 PM IST on September 30, 2026 (06:30 AM UTC)
    DATA_CUTOFF_FLOOR = pd.Timestamp("2026-09-30 06:30:00", tz="UTC")

    if not df_signals.empty:
        if df_signals['timestamp'].dt.tz is None:
            df_signals['timestamp'] = df_signals['timestamp'].dt.tz_localize('UTC')
        df_signals = df_signals[df_signals['timestamp'] >= DATA_CUTOFF_FLOOR].copy()

    if not df_payloads.empty:
        if df_payloads['timestamp'].dt.tz is None:
            df_payloads['timestamp'] = df_payloads['timestamp'].dt.tz_localize('UTC')
        df_payloads = df_payloads[df_payloads['timestamp'] >= DATA_CUTOFF_FLOOR].copy()

    if not df_signals.empty:
        df_signals['sentiment_index'] = df_signals['sentiment_score'] * 100
    if not df_payloads.empty:
        df_payloads['sentiment_index'] = df_payloads['sentiment_score'] * 100

    return df_signals, df_payloads, latest_pipeline_run


# --- Main Application Orchestrator ---

@make_fragment_decorator(run_every="5m")
def render_dashboard():
    df_signals, df_payloads, latest_pipeline_run = get_processed_data()

    if df_signals.empty:
        st.info("Database empty. Run the ingestion engine to populate.")
        return

    init_session_persistence(df_signals)
    render_local_storage_sync_script()

    render_header_banner(df_signals, latest_pipeline_run, get_processed_data_fn=get_processed_data)
    render_usp_banner()
    render_filter_toolbar(df_signals)
    render_analytics_surface(df_signals, get_processed_data_fn=get_processed_data)
    render_live_intelligence_feed(df_payloads, get_processed_data_fn=get_processed_data)
    render_forward_test_ledger_section(df_signals, get_processed_data_fn=get_processed_data)
    render_regulatory_disclaimer()


render_dashboard()
