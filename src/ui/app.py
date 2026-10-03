import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
import re
import html
import time

# Configure paths to ensure absolute resolution across Streamlit Cloud runtimes
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir, '..'))
root_dir = os.path.abspath(os.path.join(src_dir, '..'))

for p in [src_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Dynamic resilient import: guards against Streamlit daemon caching stale modules in sys.modules during hot-reloads
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

st.set_page_config(page_title="Global Sentiment Platform of Share Markets", layout="wide", initial_sidebar_state="collapsed", page_icon="📈")

# --- Dynamic Theme Mode Detection ---
is_light = bool(st.session_state.get('theme_toggle', False))

if is_light:
    theme_css_vars = """
        --bg-main: #f0f7ff;
        --bg-gradient: linear-gradient(180deg, #dbeafe 0%, #eff6ff 25%, #f8fafc 100%);
        --text-primary: #0f172a;
        --text-secondary: #334155;
        --text-muted: #64748b;
        --card-bg: rgba(255, 255, 255, 0.85);
        --card-border: rgba(148, 163, 184, 0.3);
        --card-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
        --card-hover-bg: #ffffff;
        --card-hover-border: rgba(59, 130, 246, 0.4);
        --input-bg: #ffffff;
        --input-border: rgba(148, 163, 184, 0.35);
        --input-text: #0f172a;
        --header-bg: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(224, 242, 254, 0.85) 100%);
        --header-border: rgba(59, 130, 246, 0.35);
        --header-border-left: #0284c7;
        --header-shadow: 0 4px 20px rgba(2, 132, 199, 0.08);
        --edge-bg: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 249, 255, 0.9) 100%);
        --edge-border: rgba(56, 189, 248, 0.35);
        --edge-accent: #0284c7;
        --edge-text: #334155;
        --feed-bg: rgba(255, 255, 255, 0.65);
        --feed-border: rgba(148, 163, 184, 0.25);
        --feed-card-bg: #ffffff;
        --feed-card-border: rgba(148, 163, 184, 0.2);
        --feed-card-hover: rgba(240, 249, 255, 0.95);
        --feed-headline: #0f172a;
        --feed-badge-bg: rgba(0, 0, 0, 0.04);
        --feed-badge-border: rgba(0, 0, 0, 0.08);
        --feed-badge-text: #475569;
    """
else:
    theme_css_vars = """
        --bg-main: #020617;
        --bg-gradient: #020617;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --card-bg: rgba(255, 255, 255, 0.03);
        --card-border: rgba(255, 255, 255, 0.1);
        --card-shadow: none;
        --card-hover-bg: rgba(255, 255, 255, 0.05);
        --card-hover-border: rgba(255, 255, 255, 0.2);
        --input-bg: rgba(255, 255, 255, 0.03);
        --input-border: rgba(255, 255, 255, 0.09);
        --input-text: #f8fafc;
        --header-bg: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 58, 138, 0.22) 100%);
        --header-border: rgba(59, 130, 246, 0.28);
        --header-border-left: #3b82f6;
        --header-shadow: 0 4px 20px rgba(0, 0, 0, 0.25), 0 0 15px rgba(59, 130, 246, 0.08);
        --edge-bg: linear-gradient(135deg, rgba(15, 23, 42, 0.85) 0%, rgba(30, 41, 59, 0.45) 50%, rgba(15, 23, 42, 0.85) 100%);
        --edge-border: rgba(56, 189, 248, 0.22);
        --edge-accent: #38bdf8;
        --edge-text: #cbd5e1;
        --feed-bg: rgba(255, 255, 255, 0.015);
        --feed-border: rgba(255, 255, 255, 0.08);
        --feed-card-bg: rgba(255, 255, 255, 0.02);
        --feed-card-border: rgba(255, 255, 255, 0.06);
        --feed-card-hover: rgba(255, 255, 255, 0.04);
        --feed-headline: #f8fafc;
        --feed-badge-bg: rgba(255, 255, 255, 0.04);
        --feed-badge-border: rgba(255, 255, 255, 0.08);
        --feed-badge-text: #94a3b8;
    """

# --- CSS Theme Injection ---
css_theme_template = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=Montserrat:wght@400;600;700;800&display=swap');
    
    :root {
__THEME_VARS__
    }
    
    html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'IBM Plex Sans', sans-serif;
        background: var(--bg-gradient) !important;
        background-color: var(--bg-main) !important;
        color: var(--text-primary) !important;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 1600px;
        background: transparent !important;
    }
    
    /* Professional Headers */
    .main-header, .section-header {
        font-family: 'Montserrat', sans-serif;
        font-weight: 700;
        color: var(--text-primary) !important;
    }
    .section-header {
        font-size: 1.1rem;
        margin-bottom: 15px;
    }
    
    /* Enviro Style Glass Cards */
    .white-card {
        background: var(--card-bg) !important;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        border: 1px solid var(--card-border) !important;
        box-shadow: var(--card-shadow);
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .white-card:last-child {
        margin-bottom: 0 !important;
    }
    .white-card:hover {
        background: var(--card-hover-bg) !important;
        border-color: var(--card-hover-border) !important;
    }
    
    /* Colored Glass Cards (Deep Translucent Tints) */
    .bg-blue { border-left: 3px solid #3b82f6 !important; background: rgba(59, 130, 246, 0.1) !important; }
    .bg-blue:hover { background: rgba(59, 130, 246, 0.15) !important; border-color: rgba(59, 130, 246, 0.3) !important; }
    
    .bg-green { border-left: 3px solid #10b981 !important; background: rgba(16, 185, 129, 0.1) !important; }
    .bg-green:hover { background: rgba(16, 185, 129, 0.15) !important; border-color: rgba(16, 185, 129, 0.3) !important; }
    
    .bg-purple { border-left: 3px solid #8b5cf6 !important; background: rgba(139, 92, 246, 0.1) !important; }
    .bg-purple:hover { background: rgba(139, 92, 246, 0.15) !important; border-color: rgba(139, 92, 246, 0.3) !important; }
    
    .bg-orange { border-left: 3px solid #f59e0b !important; background: rgba(245, 158, 11, 0.1) !important; }
    .bg-orange:hover { background: rgba(245, 158, 11, 0.15) !important; border-color: rgba(245, 158, 11, 0.3) !important; }
    
    .bg-indigo { border-left: 3px solid #6366f1 !important; background: rgba(99, 102, 241, 0.1) !important; }
    .bg-indigo:hover { background: rgba(99, 102, 241, 0.15) !important; border-color: rgba(99, 102, 241, 0.3) !important; }
    
    /* Override Streamlit native container border */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card-bg) !important;
        border-radius: 8px !important;
        border: 1px solid var(--card-border) !important;
        box-shadow: var(--card-shadow) !important;
    }
    
    /* Force Streamlit Columns to Stretch & Align Bottoms Flush */
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        height: 100% !important;
        flex: 1 1 auto !important;
    }
    
    /* Style Streamlit Selectbox Inputs */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 6px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: var(--input-text) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
        color: var(--input-text) !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] svg {
        fill: var(--input-text) !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover {
        border-color: rgba(59, 130, 246, 0.45) !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.15) !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-testid="stSelectboxVirtualDropdown"] {
        background: var(--input-bg) !important;
        color: var(--input-text) !important;
    }
    div[data-baseweb="menu"] li {
        color: var(--input-text) !important;
    }

    /* Top Header Row Layout & Symmetrical Cards */
    div[data-testid="stHorizontalBlock"]:first-of-type {
        margin-bottom: 14px !important;
        align-items: stretch !important;
    }
    
    /* Top Right Action Card (Backend Status & Dark Mode Toggle) */
    div[data-testid="stVerticalBlock"]:has(#header-control-card-anchor),
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(2) > div[data-testid="stVerticalBlock"] {
        background: var(--header-bg) !important;
        border: 1px solid var(--header-border) !important;
        border-left: 4px solid var(--header-border-left) !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: var(--header-shadow) !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-sizing: border-box !important;
        margin-bottom: 0 !important;
        gap: 0 !important;
    }
    
    div[data-testid="stVerticalBlock"]:has(#header-control-card-anchor) div[data-testid="stMarkdownContainer"],
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(2) div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stVerticalBlock"]:has(#header-control-card-anchor) div[data-testid="stMarkdownContainer"] > p,
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(2) div[data-testid="stMarkdownContainer"] > p {
        margin: 0 !important;
    }

    /* Style Streamlit Toggle Switch inside the Header Action Card */
    div[data-testid="stVerticalBlock"]:has(#header-control-card-anchor) div[data-testid="stToggle"],
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(2) div[data-testid="stToggle"] {
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        margin-top: 4px !important;
        margin-bottom: 0 !important;
        padding-top: 5px !important;
        border-top: 1px solid var(--card-border) !important;
    }
    div[data-testid="stVerticalBlock"]:has(#header-control-card-anchor) div[data-testid="stToggle"] label,
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(2) div[data-testid="stToggle"] label {
        display: flex !important;
        flex-direction: row-reverse !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        cursor: pointer !important;
        margin: 0 !important;
        padding: 0 !important;
        gap: 8px !important;
    }
    div[data-testid="stVerticalBlock"]:has(#header-control-card-anchor) div[data-testid="stToggle"] label p,
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"]:nth-of-type(2) div[data-testid="stToggle"] label p {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.68rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        letter-spacing: 0.04em !important;
        text-transform: uppercase !important;
        margin: 0 !important;
    }
    
    /* Metrics */
    .metric-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-primary) !important;
        letter-spacing: -0.01em;
        margin-bottom: 2px;
    }
    .metric-sub {
        font-size: 0.8rem;
        font-weight: 600;
    }
    .green { color: #10b981 !important; }
    .red { color: #ef4444 !important; } 
    .gray { color: var(--text-muted) !important; }
    
    .metric-footer {
        font-size: 0.75rem;
        color: var(--text-muted) !important;
        border-top: 1px solid var(--card-border) !important;
        padding-top: 8px;
        margin-top: 8px;
    }
    
    /* Responsive Design Adjustments */
    @media (max-width: 1024px) {
        .metric-value { font-size: 1.35rem; }
        .block-container { padding: 1rem !important; }
    }
    
    @media (max-width: 768px) {
        .metric-value { font-size: 1.2rem; }
        .metric-title { font-size: 0.7rem; }
        .white-card { padding: 10px 12px; margin-bottom: 8px; }
        div[data-testid="stHorizontalBlock"] {
            align-items: initial !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
            height: auto !important;
            justify-content: flex-start !important;
            flex: initial !important;
        }
    }

    @media (max-width: 480px) {
        .block-container { padding: 0.75rem 0.5rem !important; }
        .white-card { padding: 8px 10px; margin-bottom: 8px; }
    }

    /* Hide Streamlit native UI elements */
    header[data-testid="stHeader"] {display: none !important;}
    #MainMenu {display: none !important;}
    footer {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
    
    /* Enhanced Live News Feed Styling */
    .news-feed-container {
        background: var(--feed-bg) !important;
        border: 1px solid var(--feed-border) !important;
        border-radius: 8px;
        padding: 14px;
        max-height: 420px;
        overflow-y: auto;
    }
    .news-feed-container::-webkit-scrollbar {
        width: 6px;
    }
    .news-feed-container::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.04);
        border-radius: 4px;
    }
    .news-feed-container::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.3);
        border-radius: 4px;
    }
    .news-feed-container::-webkit-scrollbar-thumb:hover {
        background: rgba(148, 163, 184, 0.5);
    }
    
    .news-item-card {
        background: var(--feed-card-bg) !important;
        border: 1px solid var(--feed-card-border) !important;
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }
    .news-item-card:hover {
        background: var(--feed-card-hover) !important;
        border-color: rgba(59, 130, 246, 0.25) !important;
    }
    .news-item-card:last-child {
        margin-bottom: 0;
    }
    
    /* Collapsible News Feed Card & Accordion */
    details.news-feed-accordion {
        margin-top: 28px;
        margin-bottom: 14px;
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-left: 4px solid #3b82f6 !important;
        border-radius: 8px;
        transition: all 0.25s ease;
        box-shadow: var(--card-shadow) !important;
    }
    details.news-feed-accordion:hover {
        border-color: rgba(59, 130, 246, 0.35) !important;
    }
    details.news-feed-accordion summary.news-feed-summary {
        list-style: none !important;
        cursor: pointer;
        user-select: none;
        outline: none;
        padding: 12px 18px;
        transition: all 0.2s ease;
    }
    details.news-feed-accordion summary.news-feed-summary::-webkit-details-marker {
        display: none !important;
    }
    details.news-feed-accordion summary.news-feed-summary::marker {
        display: none !important;
    }
    details.news-feed-accordion summary.news-feed-summary:hover {
        background: rgba(255, 255, 255, 0.025);
    }
    details.news-feed-accordion[open] summary.news-feed-summary {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .expand-action-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(59, 130, 246, 0.18);
        border: 1px solid rgba(59, 130, 246, 0.45);
        color: #60a5fa;
        padding: 4px 12px;
        border-radius: 5px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        font-family: 'Montserrat', sans-serif;
        text-transform: uppercase;
        transition: all 0.2s ease;
        flex-shrink: 0;
    }
    details.news-feed-accordion summary.news-feed-summary:hover .expand-action-btn {
        background: rgba(59, 130, 246, 0.3);
        border-color: #60a5fa;
        color: #ffffff;
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.45);
    }
    details.news-feed-accordion .expand-text { display: inline-flex; align-items: center; gap: 5px; }
    details.news-feed-accordion .collapse-text { display: none; }
    details.news-feed-accordion[open] .expand-text { display: none; }
    details.news-feed-accordion[open] .collapse-text { display: inline-flex; align-items: center; gap: 5px; }
    
    details.news-feed-accordion[open] .expand-action-btn {
        background: rgba(148, 163, 184, 0.12);
        border-color: rgba(148, 163, 184, 0.35);
        color: #cbd5e1;
    }
    details.news-feed-accordion[open] summary.news-feed-summary:hover .expand-action-btn {
        background: rgba(239, 68, 68, 0.15);
        border-color: rgba(239, 68, 68, 0.4);
        color: #f87171;
        box-shadow: 0 0 12px rgba(239, 68, 68, 0.35);
    }
</style>
""".replace("__THEME_VARS__", theme_css_vars)

st.markdown(css_theme_template, unsafe_allow_html=True)

def clean_news_item(raw_text: str) -> dict:
    if not raw_text:
        return {"headline": "Market update", "source": ""}
    unescaped = html.unescape(str(raw_text))
    clean = re.sub(r'<[^>]+>', ' ', unescaped)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    parts = [p.strip() for p in clean.split(' - ') if p.strip()]
    if not parts:
        return {"headline": clean, "source": ""}
    
    headline = parts[0]
    source = ""
    if len(parts) > 1:
        for p in reversed(parts[1:]):
            if 1 < len(p) <= 25 and p != headline:
                source = p
                break
                
    if source and headline.endswith(f" - {source}"):
        headline = headline[:-len(f" - {source}")].strip()
        
    return {"headline": headline, "source": source}

@st.cache_data(ttl=30)
def load_data():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        now = pd.Timestamp.utcnow()
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
        return mock_signals, mock_payloads

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
            return df_signals, df_payloads
        except Exception as e:
            if attempt < max_retries - 1:
                # Connection may have dropped due to idle timeout; reset pool and retry
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
            st.error(f"Database error: {e}")
            return pd.DataFrame(), pd.DataFrame()

df_signals, df_payloads = load_data()

# Real-time regional relevance and contaminant gatekeeper:
# Dynamically eliminates legacy misclassified news items (e.g. US news under India)
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
    except Exception as filter_err:
        pass

# Real-time deduplication gatekeeper:
# Dynamically eliminates redundant entries for the same headline across multiple index tickers
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
    except Exception as dedup_err:
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
    # Calibrate historical records where magnitude was suppressed by the early rubric-score bug
    df_signals['sentiment_index'] = df_signals['sentiment_score'] * 100
    df_payloads['sentiment_index'] = df_payloads['sentiment_score'] * 100
    # --- Top Row: Header Banner (Left) & Top-Right Control Card (System Status + Theme Toggle) ---
    header_col, action_col = st.columns([0.72, 0.28])
    
    with header_col:
        st.markdown(f"""
        <div style="background: var(--header-bg); border: 1px solid var(--header-border); border-left: 4px solid var(--header-border-left); border-radius: 8px; padding: clamp(10px, 2vw, 14px) clamp(12px, 2.5vw, 20px); height: 100%; display: flex; align-items: center; backdrop-filter: blur(10px); box-shadow: var(--header-shadow); margin-bottom: 0; box-sizing: border-box;">
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <div style="background: linear-gradient(135deg, #2563eb, #3b82f6); color: #ffffff; padding: 4px 10px; border-radius: 5px; font-weight: 800; font-size: 1.1rem; letter-spacing: 1.5px; font-family: 'Montserrat', sans-serif; box-shadow: 0 0 12px rgba(59, 130, 246, 0.45); flex-shrink: 0;">GSP</div>
                <div>
                    <div style="font-size: clamp(1.02rem, 2.3vw, 1.3rem); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; font-family: 'Montserrat', sans-serif;">Global Sentiment Platform of Share Markets</div>
                    <div style="font-size: clamp(0.70rem, 1.5vw, 0.78rem); font-weight: 500; color: var(--text-muted); font-family: 'IBM Plex Sans', sans-serif;">Real-Time Global Quantitative Intelligence & Execution Engine</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with action_col:
        status_bg = "rgba(16, 185, 129, 0.12)" if is_light else "rgba(16, 185, 129, 0.15)"
        status_border = "rgba(16, 185, 129, 0.4)" if is_light else "rgba(16, 185, 129, 0.35)"
        status_text = "#059669" if is_light else "#34d399"

        st.markdown(f"""
        <div id="header-control-card-anchor" style="display: none;"></div>
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; margin-bottom: 2px;">
            <span style="font-size: 0.65rem; font-weight: 700; color: var(--text-muted); font-family: 'Montserrat', sans-serif; letter-spacing: 0.05em; text-transform: uppercase;">BACKEND</span>
            <div style="display: inline-flex; align-items: center; gap: 5px; background: {status_bg}; border: 1px solid {status_border}; color: {status_text}; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.08em; padding: 2px 8px; border-radius: 12px; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981; display: inline-block;"></span>
                SYSTEM ONLINE
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.toggle("☀️ Light Mode" if is_light else "🌙 Dark Mode", key="theme_toggle")
    
    st.markdown(f"""
<div style="background: var(--edge-bg); border: 1px solid var(--edge-border); border-left: 4px solid var(--edge-accent); border-radius: 8px; padding: clamp(10px, 2vw, 12px) clamp(12px, 2.5vw, 18px); backdrop-filter: blur(12px); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); margin-bottom: 14px;">
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
<div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
<span style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); color: {'#0284c7' if is_light else '#38bdf8'}; font-family: 'Montserrat', sans-serif; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.1em; padding: 3px 8px; border-radius: 4px; text-transform: uppercase;">THE QUANTITATIVE EDGE</span>
<span style="font-family: 'Montserrat', sans-serif; font-size: clamp(0.82rem, 1.8vw, 0.95rem); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em;">Pure Mathematical Sentiment via Contrastive Language Modeling</span>
</div>
<div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
<span style="font-size: 0.65rem; font-weight: 700; color: {'#059669' if is_light else '#34d399'}; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">DETERMINISTIC</span>
<span style="font-size: 0.65rem; font-weight: 700; color: {'#7c3aed' if is_light else '#a78bfa'}; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">OKF-CONDITIONED</span>
<span style="font-size: 0.65rem; font-weight: 700; color: {'#d97706' if is_light else '#fbbf24'}; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">ZERO HALLUCINATION</span>
</div>
</div>
<div style="font-family: 'IBM Plex Sans', sans-serif; font-size: clamp(0.78rem, 1.5vw, 0.82rem); color: var(--edge-text); line-height: 1.55; margin-bottom: 0;">
Generative LLMs suffer from prompt drift, hallucination, and confidence clustering. GSP replaces text generation with a <strong>System-One Contrastive Model (CLM-8B)</strong> that projects global news directly onto native choice probabilities: <strong style="color: {'#059669' if is_light else '#34d399'}; font-weight: 700;">P(Bullish)</strong>, <strong style="color: {'#dc2626' if is_light else '#f87171'}; font-weight: 700;">P(Bearish)</strong>, and <strong style="color: var(--text-muted); font-weight: 700;">P(Neutral)</strong>. Headlines are conditioned against regional macroeconomic policy rules (OKF), converting real-time global news into an institutional momentum score [-100, +100].
</div>
</div>
""", unsafe_allow_html=True)
    
    # --- Top Row: Styled Filter Dropdowns (5 Aligned Controls) ---
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([1.0, 0.85, 1.25, 0.95, 1.15])
    
    with filter_col1:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span style="font-size: 0.72rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Montserrat', sans-serif;">TIMEFRAME</span>
        </div>
        """, unsafe_allow_html=True)
        timeframe_options = ["1 Day", "12 Hours", "6 Hours", "4 Hours", "7 Days", "1 Month", "1 Year", "All"]
        default_tf_ix = timeframe_options.index("7 Days") if "7 Days" in timeframe_options else 4
        date_range = st.selectbox("Timeframe", timeframe_options, index=default_tf_ix, label_visibility="collapsed")
        
    with filter_col2:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
            <span style="font-size: 0.72rem; font-weight: 700; color: #a78bfa; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Montserrat', sans-serif;">REGION</span>
        </div>
        """, unsafe_allow_html=True)
        try:
            from config.market_registry import get_all_region_codes
            all_regions = get_all_region_codes()
        except Exception:
            all_regions = ["IN", "US", "UK", "JP"]
        available_regions = df_signals['market_region'].unique().tolist()
        regions = [r for r in all_regions if r in available_regions] + [r for r in available_regions if r not in all_regions]
        if not regions:
            regions = ["IN"]
        default_ix = regions.index("IN") if "IN" in regions else 0
        selected_region = st.selectbox("Region", regions, index=default_ix, label_visibility="collapsed")

    with filter_col3:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 10"></polyline></svg>
            <span style="font-size: 0.72rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Montserrat', sans-serif;">TIMEZONE</span>
        </div>
        """, unsafe_allow_html=True)
        tz_options = {
            "Asia/Kolkata (IST)": "Asia/Kolkata",
            "UTC": "UTC",
            "America/New_York (EST)": "America/New_York",
            "Europe/London (GMT)": "Europe/London",
            "Asia/Tokyo (JST)": "Asia/Tokyo"
        }
        tz_keys = list(tz_options.keys())
        default_tz_ix = next((i for i, k in enumerate(tz_keys) if "IST" in k), 0)
        display_tz = st.selectbox("tz", tz_keys, index=default_tz_ix, label_visibility="collapsed")
        target_tz = tz_options[display_tz]
        tz_abbr = display_tz.split('(')[-1].replace(')', '').strip() if '(' in display_tz else display_tz
        
    with filter_col4:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
            <span style="font-size: 0.72rem; font-weight: 700; color: #34d399; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Montserrat', sans-serif;">EMA WINDOW</span>
        </div>
        """, unsafe_allow_html=True)
        ema_options = [4, 8, 12, 24]
        default_ema_ix = ema_options.index(4) if 4 in ema_options else 0
        ema_window = st.selectbox("Exponential Moving Average (Periods)", ema_options, index=default_ema_ix, label_visibility="collapsed")
        
    with filter_col5:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 3px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
            <span style="font-size: 0.72rem; font-weight: 700; color: #fbbf24; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Montserrat', sans-serif;">CHART DISPLAY</span>
        </div>
        """, unsafe_allow_html=True)
        active_indices = df_signals[df_signals['market_region'] == selected_region]['index_ticker'].unique().tolist()
        active_indices = [x for x in active_indices if x != 'UNKNOWN']
        chart_display = st.selectbox("Chart Display", ["All Indices"] + active_indices, index=0, label_visibility="collapsed")

    filtered_signals = df_signals[df_signals['market_region'] == selected_region].copy()
    display_payloads = df_payloads.copy()
    
    # --- Implement Timeframe Filtering ---
    if not filtered_signals.empty and date_range != "All":
        # Ensure timestamp is tz-aware for accurate Timedelta math
        if filtered_signals['timestamp'].dt.tz is None:
            filtered_signals['timestamp'] = filtered_signals['timestamp'].dt.tz_localize('UTC')
        if display_payloads['timestamp'].dt.tz is None:
            display_payloads['timestamp'] = display_payloads['timestamp'].dt.tz_localize('UTC')
            
        now = pd.Timestamp.utcnow()
        if date_range in ["4 Hours", "4 Hour", "4H"]: cutoff = now - pd.Timedelta(hours=4)
        elif date_range in ["6 Hours", "6 Hour", "6H"]: cutoff = now - pd.Timedelta(hours=6)
        elif date_range in ["12 Hours", "12 Hour", "12H"]: cutoff = now - pd.Timedelta(hours=12)
        elif date_range in ["1 Day", "1Day", "24 Hours", "24 Hour", "24H"]: cutoff = now - pd.Timedelta(hours=24)
        elif date_range in ["7 Days", "7 Day", "7D"]: cutoff = now - pd.Timedelta(days=7)
        elif date_range in ["1 Month", "1M"]: cutoff = now - pd.Timedelta(days=30)
        elif date_range in ["1 Year", "1Y"]: cutoff = now - pd.Timedelta(days=365)
        
        filtered_signals = filtered_signals[filtered_signals['timestamp'] >= cutoff]
        display_payloads = display_payloads[display_payloads['timestamp'] >= cutoff]
    
    if not filtered_signals.empty:
        # Convert DataFrames to User Selected Timezone
        if filtered_signals['timestamp'].dt.tz is None:
            filtered_signals['timestamp'] = filtered_signals['timestamp'].dt.tz_localize('UTC')
        filtered_signals['timestamp'] = filtered_signals['timestamp'].dt.tz_convert(target_tz)
        
        if display_payloads['timestamp'].dt.tz is None:
            display_payloads['timestamp'] = display_payloads['timestamp'].dt.tz_localize('UTC')
        display_payloads['timestamp'] = display_payloads['timestamp'].dt.tz_convert(target_tz)

        filtered_signals.sort_values('timestamp', inplace=True)
        
        # Dynamically adjust grouping frequency based on zoom level to prevent blank charts
        freq_str = 'h'
        if date_range in ["1 Month", "1M", "1 Year", "1Y", "All"]:
            freq_str = 'D'
        
        # Calculate EMA by grouping into active periods (dropna prevents flatlines)
        df_trend = filtered_signals.groupby(pd.Grouper(key='timestamp', freq=freq_str))['sentiment_index'].mean().dropna().reset_index()
        df_trend['EMA_Index'] = df_trend['sentiment_index'].ewm(span=ema_window, adjust=False).mean()
        
        # Merge the EMA back to the latest point for KPIs
        current_ema = df_trend['EMA_Index'].iloc[-1] if len(df_trend) > 0 else 0
        previous_ema = df_trend['EMA_Index'].iloc[-2] if len(df_trend) > 1 else 0
        delta = current_ema - previous_ema
        
        # Pivot the data onto a strict chronological grid for plotting
        pivot_df = filtered_signals.pivot_table(
            index=pd.Grouper(key='timestamp', freq=freq_str),
            columns='index_ticker',
            values='sentiment_index',
            aggfunc='mean'
        ).fillna(0).reset_index()
        
        # Ensure plot timestamps are naive in target_tz so Plotly renders exact wall-clock time
        plot_trend_x = df_trend['timestamp'].dt.tz_localize(None) if df_trend['timestamp'].dt.tz is not None else df_trend['timestamp']
        plot_pivot_x = pivot_df['timestamp'].dt.tz_localize(None) if pivot_df['timestamp'].dt.tz is not None else pivot_df['timestamp']
        
        # --- Main Layout Split (1 Narrow Left, 1 Wide Right) ---
        left_col, right_col = st.columns([1.2, 4])
        
        with left_col:
            # 1. Global Index
            if delta > 0:
                arrow = "▲"
                delta_pill_color = "#34d399"
                delta_pill_bg = "rgba(16, 185, 129, 0.15)"
                delta_pill_border = "rgba(16, 185, 129, 0.3)"
            elif delta < 0:
                arrow = "▼"
                delta_pill_color = "#f87171"
                delta_pill_bg = "rgba(239, 68, 68, 0.15)"
                delta_pill_border = "rgba(239, 68, 68, 0.3)"
            else:
                arrow = "▬"
                delta_pill_color = "#94a3b8"
                delta_pill_bg = "rgba(148, 163, 184, 0.15)"
                delta_pill_border = "rgba(148, 163, 184, 0.3)"
                
            val_color = "green" if current_ema > 0 else "red" if current_ema < 0 else ""
            
            st.markdown(f"""
<div class="white-card bg-blue">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 4px;">
        <span class="metric-title" style="margin-bottom: 0;">Aggregate Optimism</span>
        <span style="font-size: 0.68rem; font-weight: 700; color: #60a5fa; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">{selected_region}</span>
    </div>
    <div class="metric-value {val_color}">{current_ema:+.1f}</div>
    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
        <span style="font-size: 0.72rem; font-weight: 700; color: {delta_pill_color}; background: {delta_pill_bg}; border: 1px solid {delta_pill_border}; padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">
            {arrow} {abs(delta):.1f}%
        </span>
        <span style="font-size: 0.72rem; color: #64748b;">vs previous period</span>
    </div>
    <div class="metric-footer" style="margin-top: 8px; padding-top: 6px; font-size: 0.72rem; color: #94a3b8; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">
        <span>Confidence Vector</span>
        <span style="color: #cbd5e1; font-weight: 600;">System-One CLM</span>
    </div>
</div>
""", unsafe_allow_html=True)
            
            # 2. Market Bias
            bias = "Bullish" if current_ema > 5 else "Bearish" if current_ema < -5 else "Neutral"
            if bias == "Bullish":
                b_color_hex = "#34d399"
                b_pill_bg = "rgba(16, 185, 129, 0.15)"
                b_pill_border = "rgba(16, 185, 129, 0.3)"
                b_val_color = "green"
            elif bias == "Bearish":
                b_color_hex = "#f87171"
                b_pill_bg = "rgba(239, 68, 68, 0.15)"
                b_pill_border = "rgba(239, 68, 68, 0.3)"
                b_val_color = "red"
            else:
                b_color_hex = "#c084fc"
                b_pill_bg = "rgba(168, 85, 247, 0.15)"
                b_pill_border = "rgba(168, 85, 247, 0.3)"
                b_val_color = ""
                
            st.markdown(f"""
<div class="white-card bg-purple">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 4px;">
        <span class="metric-title" style="margin-bottom: 0;">Market Bias</span>
        <span style="font-size: 0.68rem; font-weight: 700; color: {b_color_hex}; background: {b_pill_bg}; border: 1px solid {b_pill_border}; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">{bias}</span>
    </div>
    <div class="metric-value {b_val_color}">{bias}</div>
    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
        <span style="font-size: 0.72rem; font-weight: 700; color: #c084fc; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">
            {ema_window}-Period Window
        </span>
        <span style="font-size: 0.72rem; color: #64748b;">moving average</span>
    </div>
    <div class="metric-footer" style="margin-top: 8px; padding-top: 6px; font-size: 0.72rem; color: var(--text-muted); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">
        <span>Signal Strategy</span>
        <span style="color: var(--text-secondary); font-weight: 600;">EMA Crossover</span>
    </div>
</div>
""", unsafe_allow_html=True)
            
            # 3. Volume
            st.markdown(f"""
<div class="white-card bg-orange">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 4px;">
        <span class="metric-title" style="margin-bottom: 0;">Total News Volume</span>
        <span style="font-size: 0.68rem; font-weight: 700; color: #fbbf24; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">Live Feed</span>
    </div>
    <div class="metric-value" style="color: var(--text-primary);">{len(filtered_signals)}</div>
    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
        <span style="font-size: 0.72rem; font-weight: 700; color: #fbbf24; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">
            {date_range} Window
        </span>
        <span style="font-size: 0.72rem; color: #64748b;">articles ingested</span>
    </div>
    <div class="metric-footer" style="margin-top: 8px; padding-top: 6px; font-size: 0.72rem; color: var(--text-muted); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">
        <span>Ingestion Cycle</span>
        <span style="color: var(--text-secondary); font-weight: 600;">Every 2 Hours</span>
    </div>
</div>
""", unsafe_allow_html=True)
            
            # 4. Indices Active
            tracked_count = filtered_signals['index_ticker'].nunique()
            st.markdown(f"""
<div class="white-card bg-green">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 4px;">
        <span class="metric-title" style="margin-bottom: 0;">Tracked Indices</span>
        <span style="font-size: 0.68rem; font-weight: 700; color: #34d399; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">{selected_region}</span>
    </div>
    <div class="metric-value" style="color: var(--text-primary);">{tracked_count}</div>
    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
        <span style="font-size: 0.72rem; font-weight: 700; color: #34d399; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">
            100% Active
        </span>
        <span style="font-size: 0.72rem; color: #64748b;">real-time monitored</span>
    </div>
    <div class="metric-footer" style="margin-top: 8px; padding-top: 6px; font-size: 0.72rem; color: var(--text-muted); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">
        <span>Active Universe</span>
        <span style="color: var(--text-secondary); font-weight: 600;">20 Global Assets</span>
    </div>
</div>
""", unsafe_allow_html=True)

        with right_col:
            # --- Large Area Chart at the top of the right column ---
            with st.container(border=True):
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); padding: 5px; border-radius: 6px; display: flex; align-items: center;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                        </div>
                        <div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); font-family: 'Montserrat', sans-serif;">Aggregate Market Optimism</div>
                            <div style="font-size: 0.75rem; color: var(--text-muted); font-family: 'IBM Plex Sans', sans-serif;">Multi-Index Sentiment Surface & {selected_region} Moving Average</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                        <span style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; color: {'#0284c7' if is_light else '#60a5fa'}; background: {'rgba(2, 132, 199, 0.12)' if is_light else 'rgba(59, 130, 246, 0.12)'}; padding: 3px 8px; border-radius: 4px; border: 1px solid {'rgba(2, 132, 199, 0.25)' if is_light else 'rgba(59, 130, 246, 0.25)'}; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">
                            {selected_region} Market
                        </span>
                        <span style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; color: {'#7c3aed' if is_light else '#a78bfa'}; background: {'rgba(124, 58, 237, 0.12)' if is_light else 'rgba(168, 85, 247, 0.12)'}; padding: 3px 8px; border-radius: 4px; border: 1px solid {'rgba(124, 58, 237, 0.25)' if is_light else 'rgba(168, 85, 247, 0.25)'}; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">
                            {ema_window}-Period EMA
                        </span>
                        <span style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; color: {'#059669' if is_light else '#34d399'}; background: {'rgba(5, 150, 105, 0.12)' if is_light else 'rgba(16, 185, 129, 0.12)'}; padding: 3px 8px; border-radius: 4px; border: 1px solid {'rgba(5, 150, 105, 0.25)' if is_light else 'rgba(16, 185, 129, 0.25)'}; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">
                            AI System-One
                        </span>
                        <span style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; color: {'#0284c7' if is_light else '#38bdf8'}; background: {'rgba(2, 132, 199, 0.12)' if is_light else 'rgba(56, 189, 248, 0.12)'}; padding: 3px 8px; border-radius: 4px; border: 1px solid {'rgba(2, 132, 199, 0.25)' if is_light else 'rgba(56, 189, 248, 0.25)'}; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">
                            {tz_abbr}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                fig_area = go.Figure()
                
                # Plot overlapping filled areas for each specific Index
                colors = ["#2962FF", "#E91E63", "#FF9800", "#9C27B0", "#00BCD4"] # Sharp terminal colors
                tickers = [c for c in pivot_df.columns if c != 'timestamp']
                
                for i, ticker in enumerate(tickers):
                    if ticker == 'UNKNOWN': 
                        continue
                        
                    if chart_display != "All Indices" and ticker != chart_display:
                        continue
                        
                    fig_area.add_trace(go.Scatter(
                        x=plot_pivot_x, y=pivot_df[ticker],
                        mode='lines+markers', name=f'{ticker} Sentiment',
                        line=dict(width=1.5, color=colors[i % len(colors)]),
                        marker=dict(size=4),
                        fill='tozeroy',
                        opacity=0.3
                    ))
                
                # Add smooth thick line for Global EMA Trend on top
                fig_area.add_trace(go.Scatter(
                    x=plot_trend_x, y=df_trend['EMA_Index'],
                    mode='lines+markers',
                    line=dict(color='#0f172a' if is_light else '#f8fafc', width=2.5, shape='linear'), 
                    marker=dict(size=6, color='#0f172a' if is_light else '#f8fafc', line=dict(color='#ffffff' if is_light else '#020617', width=1)),
                    name=f'{selected_region} Mean (EMA)'
                ))
                
                fig_area.update_layout(
                    height=370, margin=dict(l=0, r=0, t=5, b=0),
                    plot_bgcolor="rgba(255,255,255,0.55)" if is_light else "rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        font=dict(color="#0f172a" if is_light else "#f8fafc", size=10, family="Montserrat")
                    ),
                    xaxis=dict(
                        showgrid=True, gridcolor='rgba(148, 163, 184, 0.22)' if is_light else 'rgba(255,255,255,0.06)',
                        showline=True, linecolor='rgba(100, 116, 139, 0.35)' if is_light else 'rgba(255,255,255,0.15)', linewidth=1,
                        ticks='outside', tickcolor='rgba(100, 116, 139, 0.35)' if is_light else 'rgba(255,255,255,0.25)', ticklen=4,
                        title=dict(text=f"<b>TIMELINE • {tz_abbr}</b>", font=dict(size=11, color="#0284c7" if is_light else "#38bdf8", family="Montserrat")),
                        tickfont=dict(size=10, color="#334155" if is_light else "#94a3b8", family="IBM Plex Sans")
                    ),
                    yaxis=dict(
                        showgrid=True, gridcolor='rgba(148, 163, 184, 0.22)' if is_light else 'rgba(255,255,255,0.06)',
                        zeroline=True, zerolinecolor='rgba(16, 185, 129, 0.65)' if is_light else 'rgba(16, 185, 129, 0.45)', zerolinewidth=1.5,
                        showline=True, linecolor='rgba(100, 116, 139, 0.35)' if is_light else 'rgba(255,255,255,0.15)', linewidth=1,
                        ticks='outside', tickcolor='rgba(100, 116, 139, 0.35)' if is_light else 'rgba(255,255,255,0.25)', ticklen=4,
                        title=dict(text="<b>OPTIMISM SCORE</b>", font=dict(size=11, color="#0284c7" if is_light else "#38bdf8", family="Montserrat")),
                        tickfont=dict(size=10, color="#0f172a" if is_light else "#f8fafc", family="IBM Plex Sans", weight="bold"),
                        side="right"
                    )
                )
                st.plotly_chart(fig_area, use_container_width=True)

            # --- Mini KPI Tiles for Individual Indices (Dynamic Sentiment Styling) ---
            valid_tickers = [t for t in tickers if t != 'UNKNOWN']
            if valid_tickers:
                kpi_html = '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;">'
                
                for ticker in valid_tickers:
                    latest_score = pivot_df[ticker].iloc[-1] if len(pivot_df) > 0 else 0
                    prev_score = pivot_df[ticker].iloc[-2] if len(pivot_df) > 1 else 0
                    delta_idx = latest_score - prev_score
                    
                    if abs(latest_score) < 0.5:
                        ticker_status = "NEUTRAL"
                        t_status_color = "#475569" if is_light else "#94a3b8"
                        t_status_bg = "rgba(148, 163, 184, 0.18)" if is_light else "rgba(148, 163, 184, 0.12)"
                        t_status_border = "rgba(148, 163, 184, 0.35)" if is_light else "rgba(148, 163, 184, 0.3)"
                        t_card_border = "#94a3b8" if is_light else "#64748b"
                        t_val_color = "#334155" if is_light else "#cbd5e1"
                    elif latest_score >= 0.5:
                        ticker_status = "BULLISH"
                        t_status_color = "#059669" if is_light else "#34d399"
                        t_status_bg = "rgba(16, 185, 129, 0.15)"
                        t_status_border = "rgba(16, 185, 129, 0.35)"
                        t_card_border = "#10b981"
                        t_val_color = "#059669" if is_light else "#10b981"
                    else:
                        ticker_status = "BEARISH"
                        t_status_color = "#dc2626" if is_light else "#f87171"
                        t_status_bg = "rgba(239, 68, 68, 0.15)"
                        t_status_border = "rgba(239, 68, 68, 0.35)"
                        t_card_border = "#ef4444"
                        t_val_color = "#dc2626" if is_light else "#ef4444"
                    
                    if delta_idx > 0:
                        d_arrow = "▲"
                        d_pill_color = "#059669" if is_light else "#34d399"
                        d_pill_bg = "rgba(16, 185, 129, 0.12)"
                        d_pill_border = "rgba(16, 185, 129, 0.25)"
                    elif delta_idx < 0:
                        d_arrow = "▼"
                        d_pill_color = "#dc2626" if is_light else "#f87171"
                        d_pill_bg = "rgba(239, 68, 68, 0.12)"
                        d_pill_border = "rgba(239, 68, 68, 0.25)"
                    else:
                        d_arrow = "▬"
                        d_pill_color = "#475569" if is_light else "#94a3b8"
                        d_pill_bg = "rgba(148, 163, 184, 0.12)"
                        d_pill_border = "rgba(148, 163, 184, 0.25)"
                    
                    kpi_html += f"""
<div class="news-item-card" style="flex: 1 1 120px; padding: 10px 12px; border-left: 3px solid {t_card_border}; margin-bottom: 0;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <span style="font-family: 'Montserrat', sans-serif; font-size: 0.75rem; font-weight: 700; color: {'#0f172a' if is_light else '#f8fafc'}; text-transform: uppercase; letter-spacing: 0.03em;">{ticker}</span>
        <span style="font-family: 'Montserrat', sans-serif; font-size: 0.65rem; font-weight: 800; color: {t_status_color}; background: {t_status_bg}; border: 1px solid {t_status_border}; padding: 1px 6px; border-radius: 4px; letter-spacing: 0.04em;">{ticker_status}</span>
    </div>
    <div style="font-family: 'Montserrat', sans-serif; font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight: 800; color: {t_val_color}; margin: 2px 0;">{latest_score:+.1f}</div>
    <div style="display: flex; align-items: center; gap: 5px; margin-top: 4px;">
        <span style="font-size: 0.72rem; font-weight: 700; color: {d_pill_color}; background: {d_pill_bg}; border: 1px solid {d_pill_border}; padding: 1px 6px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">{d_arrow} {abs(delta_idx):.1f}%</span>
        <span style="font-size: 0.7rem; color: {'#64748b' if is_light else '#94a3b8'};">momentum</span>
    </div>
</div>
"""
                
                kpi_html += '</div>'
                st.markdown(kpi_html, unsafe_allow_html=True)

        # --- Regional News Feeds at the Bottom (Full Width) ---
        region_payloads = display_payloads[display_payloads['market_region'] == selected_region]
        if not region_payloads.empty:
            region_payloads = region_payloads.sort_values('timestamp', ascending=False)
        total_events = len(region_payloads)
        bullish_count = int((region_payloads['sentiment_index'] >= 0.5).sum()) if not region_payloads.empty else 0
        bearish_count = int((region_payloads['sentiment_index'] <= -0.5).sum()) if not region_payloads.empty else 0
        noise_count = total_events - bullish_count - bearish_count
        
        html_feed = (
            f'<details class="news-feed-accordion">'
            f'<summary class="news-feed-summary" title="Click anywhere on this card to expand or collapse feed">'
            f'<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">'
            f'<div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">'
            f'<div style="display: flex; align-items: center; gap: 10px;">'
            f'<span style="display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: #3b82f6; box-shadow: 0 0 10px #3b82f6; flex-shrink: 0;"></span>'
            f'<span style="font-size: clamp(0.95rem, 2vw, 1.15rem); font-weight: 700; color: {"#0f172a" if is_light else "#f8fafc"}; font-family: \'Montserrat\', sans-serif;">{selected_region} Live Intelligence Feed</span>'
            f'</div>'
            f'<div class="expand-action-btn">'
            f'<span class="expand-text">EXPAND FEED <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg></span>'
            f'<span class="collapse-text">COLLAPSE FEED <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"></polyline></svg></span>'
            f'</div>'
            f'</div>'
            f'<div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">'
            f'<span style="font-size: 0.72rem; font-weight: 700; color: {"#0f172a" if is_light else "#f8fafc"}; background: {"rgba(0, 0, 0, 0.05)" if is_light else "rgba(255, 255, 255, 0.06)"}; border: 1px solid {"rgba(0, 0, 0, 0.1)" if is_light else "rgba(255, 255, 255, 0.12)"}; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; font-family: \'Montserrat\', sans-serif;">{total_events} Total</span>'
            f'<span style="font-size: 0.72rem; font-weight: 700; color: {"#059669" if is_light else "#34d399"}; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 4px; text-transform: uppercase; font-family: \'Montserrat\', sans-serif;">{bullish_count} Bullish</span>'
            f'<span style="font-size: 0.72rem; font-weight: 700; color: {"#dc2626" if is_light else "#f87171"}; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); padding: 3px 8px; border-radius: 4px; text-transform: uppercase; font-family: \'Montserrat\', sans-serif;">{bearish_count} Bearish</span>'
            f'<span style="font-size: 0.72rem; font-weight: 700; color: {"#475569" if is_light else "#cbd5e1"}; background: {"rgba(148, 163, 184, 0.2)" if is_light else "rgba(148, 163, 184, 0.18)"}; border: 1px solid {"rgba(148, 163, 184, 0.35)" if is_light else "rgba(148, 163, 184, 0.4)"}; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; font-family: \'Montserrat\', sans-serif;">{noise_count} Noise</span>'
            f'</div>'
            f'</div>'
            f'</summary>'
            f'<div class="news-feed-container" style="border: none !important; border-top: 1px solid rgba(255,255,255,0.06) !important; border-radius: 0 0 8px 8px; background: transparent !important; padding: 14px 18px; margin-top: 0; max-height: 440px; overflow-y: auto;">'
        )

        if not region_payloads.empty:
            for _, row in region_payloads.iterrows():
                sentiment = row['sentiment_index']
                if date_range in ["4 Hours", "4 Hour", "4H", "6 Hours", "6 Hour", "6H", "12 Hours", "12 Hour", "12H", "1 Day", "1Day", "24 Hours", "24 Hour", "24H"]:
                    time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M')
                else:
                    time_str = pd.to_datetime(row['timestamp']).strftime('%b %d, %H:%M')
                ticker_label = row.get('index_ticker', 'Macro')
                
                parsed = clean_news_item(row['raw_text'])
                clean_headline = parsed['headline']
                source = parsed['source']
                
                # Determine Sentiment & Noise status
                if abs(sentiment) < 0.5:
                    status_badge = f'<span style="background: {"rgba(148, 163, 184, 0.2)" if is_light else "rgba(148, 163, 184, 0.18)"}; border: 1px solid {"rgba(148, 163, 184, 0.35)" if is_light else "rgba(148, 163, 184, 0.45)"}; color: {"#475569" if is_light else "#cbd5e1"}; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.06em; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">NOISE</span>'
                    score_color = "#64748b" if is_light else "#94a3b8"
                    score_bg = "rgba(148, 163, 184, 0.15)" if is_light else "rgba(148, 163, 184, 0.12)"
                    score_border = "rgba(148, 163, 184, 0.35)" if is_light else "rgba(148, 163, 184, 0.3)"
                    card_border = "#94a3b8" if is_light else "#64748b"
                elif sentiment >= 0.5:
                    status_badge = f'<span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: {"#059669" if is_light else "#34d399"}; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.06em; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">BULLISH</span>'
                    score_color = "#059669" if is_light else "#10b981"
                    score_bg = "rgba(16, 185, 129, 0.15)" if is_light else "rgba(16, 185, 129, 0.12)"
                    score_border = "rgba(16, 185, 129, 0.35)" if is_light else "rgba(16, 185, 129, 0.3)"
                    card_border = "#10b981"
                else:
                    status_badge = f'<span style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: {"#dc2626" if is_light else "#f87171"}; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.06em; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">BEARISH</span>'
                    score_color = "#dc2626" if is_light else "#ef4444"
                    score_bg = "rgba(239, 68, 68, 0.15)" if is_light else "rgba(239, 68, 68, 0.12)"
                    score_border = "rgba(239, 68, 68, 0.35)" if is_light else "rgba(239, 68, 68, 0.3)"
                    card_border = "#ef4444"
                
                source_badge = f'<span style="background: {"rgba(0, 0, 0, 0.04)" if is_light else "rgba(255, 255, 255, 0.04)"}; border: 1px solid {"rgba(0, 0, 0, 0.08)" if is_light else "rgba(255, 255, 255, 0.08)"}; color: {"#475569" if is_light else "#94a3b8"}; padding: 2px 6px; border-radius: 4px; font-size: 0.68rem; font-weight: 600; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">{source}</span>' if source else ""
                
                escaped_headline = html.escape(clean_headline)
                badges_markup = (
                    f'<span style="font-family: \'IBM Plex Sans\', sans-serif; font-size: 0.75rem; font-weight: 500; color: {"#475569" if is_light else "#94a3b8"}; background: {"rgba(0,0,0,0.04)" if is_light else "rgba(255,255,255,0.04)"}; border: 1px solid {"rgba(0,0,0,0.08)" if is_light else "rgba(255,255,255,0.08)"}; padding: 2px 7px; border-radius: 4px; flex-shrink: 0;">{time_str}</span>'
                    f'<span style="font-family: \'Montserrat\', sans-serif; font-size: 0.75rem; font-weight: 700; color: {"#0284c7" if is_light else "#f8fafc"}; background: {"rgba(2, 132, 199, 0.12)" if is_light else "rgba(59, 130, 246, 0.15)"}; border: 1px solid {"rgba(2, 132, 199, 0.3)" if is_light else "rgba(59, 130, 246, 0.35)"}; padding: 2px 8px; border-radius: 4px; flex-shrink: 0;">{ticker_label}</span>'
                    f'{source_badge}{status_badge}'
                )
                score_markup = f'<div style="flex-shrink: 0;"><span style="font-family: \'Montserrat\', sans-serif; font-size: 0.8rem; font-weight: 700; color: {score_color}; background: {score_bg}; border: 1px solid {score_border}; padding: 3px 9px; border-radius: 4px; letter-spacing: 0.02em;">{sentiment:+.1f}</span></div>'
                card_top = f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;"><div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">{badges_markup}</div>{score_markup}</div>'
                card_body = f'<div style="font-size: 0.92rem; color: {"#0f172a" if is_light else "#f8fafc"}; font-weight: 500; line-height: 1.5; font-family: \'IBM Plex Sans\', sans-serif;">{escaped_headline}</div>'
                
                html_feed += f'<div class="news-item-card" style="border-left: 3px solid {card_border};">{card_top}{card_body}</div>'
        else:
            html_feed += f'<div style="color: #94a3b8; font-size: 0.88rem; padding: 18px; text-align: center; font-family: \'IBM Plex Sans\', sans-serif;">No recent news events for {selected_region} in the selected timeframe.</div>'

        html_feed += '</div></details>'
        st.markdown(html_feed, unsafe_allow_html=True)
            

    else:
        st.warning("No data found for the selected parameters.")
else:
    st.info("Database empty. Run the ingestion engine to populate.")
