"""
State persistence module for Valence.
Handles bidirectional synchronization between Streamlit session state,
URL query parameters, and browser localStorage fallback.
"""
import streamlit as st
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd

TIMEFRAME_MAP: Dict[str, str] = {
    "7D": "7 Days", "7 Days": "7 Days", "7d": "7 Days",
    "1D": "1 Day", "1 Day": "1 Day", "1d": "1 Day",
    "12H": "12 Hours", "12 Hours": "12 Hours", "12h": "12 Hours",
    "6H": "6 Hours", "6 Hours": "6 Hours", "6h": "6 Hours",
    "4H": "4 Hours", "4 Hours": "4 Hours", "4h": "4 Hours",
    "1M": "1 Month", "1 Month": "1 Month", "1m": "1 Month",
    "1Y": "1 Year", "1 Year": "1 Year", "1y": "1 Year",
    "All": "All", "all": "All"
}

TIMEFRAME_TO_QP: Dict[str, str] = {
    "7 Days": "7D",
    "1 Day": "1D",
    "12 Hours": "12H",
    "6 Hours": "6H",
    "4 Hours": "4H",
    "1 Month": "1M",
    "1 Year": "1Y",
    "All": "All"
}

REGION_MAP: Dict[str, str] = {
    "IN": "India (IN)", "India (IN)": "India (IN)", "India": "India (IN)",
    "US": "United States (US)", "United States (US)": "United States (US)", "United States": "United States (US)",
    "UK": "United Kingdom (UK)", "United Kingdom (UK)": "United Kingdom (UK)", "United Kingdom": "United Kingdom (UK)",
    "JP": "Japan (JP)", "Japan (JP)": "Japan (JP)", "Japan": "Japan (JP)"
}

REGION_TO_QP: Dict[str, str] = {
    "India (IN)": "IN",
    "United States (US)": "US",
    "United Kingdom (UK)": "UK",
    "Japan (JP)": "JP"
}

TZ_MAP: Dict[str, str] = {
    "IST": "Asia/Kolkata (IST)", "Asia/Kolkata (IST)": "Asia/Kolkata (IST)", "Asia/Kolkata": "Asia/Kolkata (IST)",
    "UTC": "UTC",
    "EST": "America/New_York (EST)", "America/New_York (EST)": "America/New_York (EST)", "America/New_York": "America/New_York (EST)",
    "GMT": "Europe/London (GMT)", "Europe/London (GMT)": "Europe/London (GMT)", "Europe/London": "Europe/London (GMT)",
    "JST": "Asia/Tokyo (JST)", "Asia/Tokyo (JST)": "Asia/Tokyo (JST)", "Asia/Tokyo": "Asia/Tokyo (JST)"
}

TZ_TO_QP: Dict[str, str] = {
    "Asia/Kolkata (IST)": "IST",
    "UTC": "UTC",
    "America/New_York (EST)": "EST",
    "Europe/London (GMT)": "GMT",
    "Asia/Tokyo (JST)": "JST"
}

EMA_MAP: Dict[str, str] = {
    "4": "4 Periods", "4 Periods": "4 Periods", "4p": "4 Periods",
    "8": "8 Periods", "8 Periods": "8 Periods", "8p": "8 Periods",
    "12": "12 Periods", "12 Periods": "12 Periods", "12p": "12 Periods",
    "24": "24 Periods", "24 Periods": "24 Periods", "24p": "24 Periods"
}

EMA_TO_QP: Dict[str, str] = {
    "4 Periods": "4",
    "8 Periods": "8",
    "12 Periods": "12",
    "24 Periods": "24"
}

FEED_MAP: Dict[str, str] = {
    "all": "All", "All": "All",
    "bullish": "Bullish", "Bullish": "Bullish",
    "bearish": "Bearish", "Bearish": "Bearish",
    "neutral": "Neutral", "Neutral": "Neutral"
}

FEED_TO_QP: Dict[str, str] = {
    "All": "all",
    "Bullish": "bullish",
    "Bearish": "bearish",
    "Neutral": "neutral"
}


def _get_query_param(key: str) -> Optional[str]:
    """Safely reads a single query parameter value from st.query_params."""
    try:
        if hasattr(st, "query_params"):
            val = st.query_params.get(key)
            if val is not None:
                if isinstance(val, list):
                    return str(val[0]) if len(val) > 0 else None
                return str(val)
    except Exception:
        pass
    return None


def _set_query_param(key: str, value: str) -> None:
    """Safely sets a query parameter value in st.query_params."""
    try:
        if hasattr(st, "query_params"):
            st.query_params[key] = value
    except Exception:
        pass


def sync_preference_to_query_params(param_key: str, value: Any) -> None:
    """
    Serializes a UI selection into the corresponding concise query parameter.
    Called when widgets change to maintain URL synchronization.
    """
    if not value:
        return

    val_str = str(value).strip()
    if param_key == "filter_timeframe":
        qp_val = TIMEFRAME_TO_QP.get(val_str, val_str)
        _set_query_param("tf", qp_val)
    elif param_key == "filter_region":
        qp_val = REGION_TO_QP.get(val_str, val_str)
        _set_query_param("region", qp_val)
    elif param_key == "filter_timezone":
        qp_val = TZ_TO_QP.get(val_str, val_str)
        _set_query_param("tz", qp_val)
    elif param_key == "filter_ema_window":
        qp_val = EMA_TO_QP.get(val_str, val_str)
        _set_query_param("ema", qp_val)
    elif param_key == "filter_chart_display":
        qp_val = "All" if val_str == "All Indices" else val_str
        _set_query_param("chart", qp_val)
    elif param_key in ("feed", "feed_sentiment_pills", "feed_sentiment_category"):
        prefix = val_str.split()[0] if val_str else "All"
        qp_val = FEED_TO_QP.get(prefix, prefix.lower())
        _set_query_param("feed", qp_val)


def sync_all_preferences_to_query_params() -> None:
    """Synchronizes all active session state preferences to st.query_params."""
    if "filter_timeframe" in st.session_state:
        sync_preference_to_query_params("filter_timeframe", st.session_state["filter_timeframe"])
    if "filter_region" in st.session_state:
        sync_preference_to_query_params("filter_region", st.session_state["filter_region"])
    if "filter_timezone" in st.session_state:
        sync_preference_to_query_params("filter_timezone", st.session_state["filter_timezone"])
    if "filter_ema_window" in st.session_state:
        sync_preference_to_query_params("filter_ema_window", st.session_state["filter_ema_window"])
    if "filter_chart_display" in st.session_state:
        sync_preference_to_query_params("filter_chart_display", st.session_state["filter_chart_display"])
    if "feed_sentiment_category" in st.session_state:
        sync_preference_to_query_params("feed", st.session_state["feed_sentiment_category"])



def init_session_persistence(df_signals: Optional[pd.DataFrame] = None) -> None:
    """
    Initializes session state from st.query_params on initial load or browser refresh.
    Enforces validation against available datasets and updates query params if absent.
    """
    # 1. Resolve Timeframe
    qp_tf = _get_query_param("tf") or _get_query_param("timeframe")
    resolved_tf = TIMEFRAME_MAP.get(qp_tf, "7 Days") if qp_tf else "7 Days"
    if "filter_timeframe" not in st.session_state or qp_tf:
        st.session_state["filter_timeframe"] = resolved_tf

    # 2. Resolve Region
    qp_region = _get_query_param("region")
    resolved_region = REGION_MAP.get(qp_region, "India (IN)") if qp_region else "India (IN)"
    if "filter_region" not in st.session_state or qp_region:
        st.session_state["filter_region"] = resolved_region

    # 3. Resolve Timezone
    qp_tz = _get_query_param("tz") or _get_query_param("timezone")
    resolved_tz = TZ_MAP.get(qp_tz, "Asia/Kolkata (IST)") if qp_tz else "Asia/Kolkata (IST)"
    if "filter_timezone" not in st.session_state or qp_tz:
        st.session_state["filter_timezone"] = resolved_tz

    # 4. Resolve EMA Window
    qp_ema = _get_query_param("ema") or _get_query_param("ema_window")
    resolved_ema = EMA_MAP.get(qp_ema, "4 Periods") if qp_ema else "4 Periods"
    if "filter_ema_window" not in st.session_state or qp_ema:
        st.session_state["filter_ema_window"] = resolved_ema

    # 5. Resolve Chart Display & Validate cross-region ticker affinity
    qp_chart = _get_query_param("chart")
    active_region_code = REGION_TO_QP.get(st.session_state["filter_region"], "IN")
    
    available_tickers: List[str] = []
    if df_signals is not None and not df_signals.empty and "market_region" in df_signals.columns and "index_ticker" in df_signals.columns:
        available_tickers = df_signals[df_signals["market_region"] == active_region_code]["index_ticker"].unique().tolist()
        available_tickers = [t for t in available_tickers if t != "UNKNOWN"]

    resolved_chart = "All Indices"
    if qp_chart and qp_chart not in ("All", "All Indices"):
        if qp_chart in available_tickers:
            resolved_chart = qp_chart
        else:
            resolved_chart = "All Indices"

    if "filter_chart_display" not in st.session_state or qp_chart:
        st.session_state["filter_chart_display"] = resolved_chart

    # 6. Resolve Live Feed Sentiment Filter
    qp_feed = _get_query_param("feed") or _get_query_param("sentiment")
    resolved_feed = FEED_MAP.get(qp_feed, "All") if qp_feed else "All"
    if "feed_sentiment_category" not in st.session_state or qp_feed:
        st.session_state["feed_sentiment_category"] = resolved_feed

    # 7. Mirror active state to query parameters so address bar is permanently in sync
    sync_preference_to_query_params("filter_timeframe", st.session_state["filter_timeframe"])
    sync_preference_to_query_params("filter_region", st.session_state["filter_region"])
    sync_preference_to_query_params("filter_timezone", st.session_state["filter_timezone"])
    sync_preference_to_query_params("filter_ema_window", st.session_state["filter_ema_window"])
    sync_preference_to_query_params("filter_chart_display", st.session_state["filter_chart_display"])
    sync_preference_to_query_params("feed", st.session_state["feed_sentiment_category"])


def get_persisted_feed_index(options: List[str], default_ix: int = 0) -> int:
    """
    Finds the index of the sentiment pill in options matching the persisted sentiment category.
    Handles dynamic count labels (e.g. 'Bullish 42' matching category 'Bullish').
    """
    active_cat = st.session_state.get("feed_sentiment_category")
    if not active_cat:
        qp_feed = _get_query_param("feed") or _get_query_param("sentiment")
        active_cat = FEED_MAP.get(qp_feed, "All") if qp_feed else "All"

    if active_cat:
        for ix, opt in enumerate(options):
            if opt.lower().startswith(active_cat.lower()):
                return ix
    return default_ix


def render_local_storage_sync_script() -> None:
    """
    Renders a transparent client-side JavaScript snippet that mirrors query params
    into localStorage and restores them if a user navigates to a bare root URL.
    """
    st.markdown("""
    <script>
    (function() {
        try {
            // 1. If URL has query parameters, persist them to localStorage
            if (window.location.search && window.location.search.length > 1) {
                localStorage.setItem('valence_persisted_query', window.location.search);
            } else {
                // 2. If URL is bare (no query params), check if localStorage has saved state
                var saved = localStorage.getItem('valence_persisted_query');
                if (saved && saved.startsWith('?') && saved.length > 1) {
                    if (!window.sessionStorage.getItem('valence_explicit_reset')) {
                        window.location.replace(window.location.pathname + saved);
                    }
                }
            }
        } catch (e) {
            // LocalStorage blocked or restricted
        }
    })();
    </script>
    """, unsafe_allow_html=True)
