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
if 'theme_toggle' not in st.session_state:
    st.session_state['theme_toggle'] = True

is_dark = bool(st.session_state.get('theme_toggle', True))
is_light = not is_dark

if is_light:
    theme_css_vars = """
        color-scheme: light !important;
        --primary-color: #0284c7 !important;
        --background-color: #f8fafc !important;
        --secondary-background-color: #ffffff !important;
        --text-color: #0f172a !important;
        --bg-main: #f8fafc;
        --bg-gradient: #f8fafc;
        --text-primary: #0f172a;
        --text-secondary: #334155;
        --text-muted: #475569;
        --card-bg: #ffffff;
        --card-border: #cbd5e1;
        --card-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
        --card-hover-bg: #ffffff;
        --card-hover-border: #94a3b8;
        --input-bg: #ffffff;
        --input-border: #cbd5e1;
        --input-text: #0f172a;
        --header-bg: #ffffff;
        --header-border: #cbd5e1;
        --header-border-left: #0284c7;
        --header-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
        --edge-bg: #ffffff;
        --edge-border: #cbd5e1;
        --edge-accent: #0284c7;
        --edge-text: #334155;
        --feed-bg: #ffffff;
        --feed-border: #cbd5e1;
        --feed-card-bg: #ffffff;
        --feed-card-border: #e2e8f0;
        --feed-card-hover: #f8fafc;
        --feed-headline: #0f172a;
        --feed-badge-bg: #f1f5f9;
        --feed-badge-border: #cbd5e1;
        --feed-badge-text: #334155;
        --action-btn-bg: rgba(2, 132, 199, 0.12);
        --action-btn-border: rgba(2, 132, 199, 0.35);
        --action-btn-color: #0284c7;
        --action-btn-hover-bg: rgba(2, 132, 199, 0.22);
        --action-btn-hover-border: #0284c7;
        --action-btn-hover-color: #0369a1;
        --metric-green: #059669;
        --metric-red: #dc2626;
        --toggle-track-bg: #cbd5e1;
        --toggle-track-border: #94a3b8;
    """
else:
    theme_css_vars = """
        color-scheme: dark !important;
        --primary-color: #10b981 !important;
        --background-color: #020617 !important;
        --secondary-background-color: #0b1329 !important;
        --text-color: #f8fafc !important;
        --bg-main: #020617;
        --bg-gradient: #020617;
        --text-primary: #f8fafc;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --card-bg: rgba(15, 23, 42, 0.65);
        --card-border: rgba(255, 255, 255, 0.08);
        --card-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        --card-hover-bg: rgba(30, 41, 59, 0.75);
        --card-hover-border: rgba(59, 130, 246, 0.4);
        --input-bg: #0b1329;
        --input-border: rgba(255, 255, 255, 0.12);
        --input-text: #f8fafc;
        --header-bg: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 58, 138, 0.28) 100%);
        --header-border: rgba(59, 130, 246, 0.35);
        --header-border-left: #3b82f6;
        --header-shadow: 0 4px 20px rgba(0, 0, 0, 0.35), 0 0 15px rgba(59, 130, 246, 0.1);
        --edge-bg: linear-gradient(135deg, rgba(15, 23, 42, 0.88) 0%, rgba(30, 41, 59, 0.5) 50%, rgba(15, 23, 42, 0.88) 100%);
        --edge-border: rgba(56, 189, 248, 0.25);
        --edge-accent: #38bdf8;
        --edge-text: #cbd5e1;
        --feed-bg: rgba(15, 23, 42, 0.5);
        --feed-border: rgba(255, 255, 255, 0.08);
        --feed-card-bg: rgba(15, 23, 42, 0.65);
        --feed-card-border: rgba(255, 255, 255, 0.07);
        --feed-card-hover: rgba(30, 41, 59, 0.8);
        --feed-headline: #f8fafc;
        --feed-badge-bg: rgba(255, 255, 255, 0.04);
        --feed-badge-border: rgba(255, 255, 255, 0.08);
        --feed-badge-text: #94a3b8;
        --action-btn-bg: rgba(59, 130, 246, 0.18);
        --action-btn-border: rgba(59, 130, 246, 0.45);
        --action-btn-color: #60a5fa;
        --action-btn-hover-bg: rgba(59, 130, 246, 0.3);
        --action-btn-hover-border: #60a5fa;
        --action-btn-hover-color: #ffffff;
        --metric-green: #10b981;
        --metric-red: #ef4444;
        --toggle-track-bg: #334155;
        --toggle-track-border: #475569;
    """

# --- CSS Theme Injection ---
css_theme_template = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=Montserrat:wght@400;600;700;800&display=swap');
    
    :root, .stApp, html, body {
__THEME_VARS__
    }
    
    html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'IBM Plex Sans', sans-serif;
        background: var(--bg-gradient) !important;
        background-color: var(--bg-main) !important;
        color: var(--text-primary) !important;
    }
    
    .block-container {
        padding-top: 1rem !important;
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
    
    /* Institutional Terminal Neutral Cards */
    .white-card {
        background: var(--card-bg) !important;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        border: 1px solid var(--card-border) !important;
        box-shadow: var(--card-shadow);
        backdrop-filter: blur(10px);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .white-card:last-child {
        margin-bottom: 0 !important;
    }
    .white-card:hover {
        background: var(--card-hover-bg) !important;
        border-color: var(--card-hover-border) !important;
    }
    .kpi-card {
        border: 1px solid var(--card-border) !important;
    }
    
    /* Override Streamlit native container and expander border */
    [data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stExpander"],
    details[data-testid="stExpander"] {
        background: var(--card-bg) !important;
        border-radius: 8px !important;
        border: 1px solid var(--card-border) !important;
        box-shadow: var(--card-shadow) !important;
    }
    
    /* Main Dashboard Content Layout (Align Left KPI Cards and Right Chart Bottoms Flush) */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) {
        align-items: stretch !important;
        margin-bottom: 12px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        flex: 1 1 auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) div[data-testid="stElementContainer"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) div[data-testid="element-container"]:has(.kpi-column-container) {
        height: 100% !important;
        flex: 1 1 auto !important;
        display: flex !important;
        flex-direction: column !important;
    }
    .kpi-column-container {
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        height: 100% !important;
        gap: 8px !important;
    }
    .kpi-column-container .kpi-card {
        flex: 1 1 0px !important;
        margin-bottom: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        padding: 9px 12px !important;
        box-sizing: border-box !important;
    }
    /* Ensure the right column container card stretches to match left column */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlock"]:has(div[data-testid="stPlotlyChart"]) {
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-sizing: border-box !important;
    }

    /* Filter Toolbar Card Enclosure (Ultra-Compact, Identical Alignment Across All 5 Columns) */
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] div[data-testid="stSelectbox"]),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stSelectbox"]),
    div[data-testid="stElementContainer"]:has(div[data-testid="stSelectbox"]) > div[data-testid="stVerticalBlock"] {
        padding: 8px 14px 10px 14px !important;
        margin-top: 0 !important;
        margin-bottom: 12px !important;
        gap: 0 !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] div[data-testid="stSelectbox"]) > div[data-testid="stHorizontalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stSelectbox"]) > div[data-testid="stHorizontalBlock"] {
        align-items: flex-start !important;
        gap: 8px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /* All 5 Filter Columns - Symmetrical & Uniform */
    div[data-testid="stColumn"]:has(div[data-testid="stSelectbox"]),
    div[data-testid="column"]:has(div[data-testid="stSelectbox"]) {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    div[data-testid="stColumn"]:has(div[data-testid="stSelectbox"]) > div[data-testid="stVerticalBlock"],
    div[data-testid="column"]:has(div[data-testid="stSelectbox"]) > div[data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        gap: 4px !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    div[data-testid="stColumn"]:has(div[data-testid="stSelectbox"]) [data-testid="stElementContainer"],
    div[data-testid="column"]:has(div[data-testid="stSelectbox"]) [data-testid="stElementContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stColumn"]:has(div[data-testid="stSelectbox"]) div[data-testid="stMarkdownContainer"],
    div[data-testid="column"]:has(div[data-testid="stSelectbox"]) div[data-testid="stMarkdownContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stColumn"]:has(div[data-testid="stSelectbox"]) div[data-testid="stMarkdownContainer"] > p,
    div[data-testid="column"]:has(div[data-testid="stSelectbox"]) div[data-testid="stMarkdownContainer"] > p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.2 !important;
    }
    div[data-testid="stSelectbox"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Eliminate redundant or collapsed selectbox labels across the board */
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        visibility: hidden !important;
        overflow: hidden !important;
        line-height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
    div[data-testid="stSelectbox"] div[role="group"] {
        min-height: 34px !important;
        height: 34px !important;
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }

    /* Style Streamlit Selectbox Inputs & Overrides (Adobe React-Aria & BaseWeb, Both Themes) */
    html body div[data-testid="stSelectbox"] div[role="group"],
    html body div[data-testid="stSelectbox"] [data-rac][role="group"],
    html body div[data-testid="stSelectbox"] .react-aria-ComboBox div[role="group"],
    html body [data-baseweb="select"],
    html body [data-baseweb="select"] > div,
    html body [data-baseweb="select"] div[role="combobox"],
    html body div[data-testid="stSelectbox"] [data-baseweb="select"],
    html body div[data-testid="stSelectbox"] [data-baseweb="select"] > div,
    html body div[data-testid="stSelectbox"] [data-baseweb="select"] div[role="combobox"] {
        background: var(--input-bg) !important;
        background-color: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 6px !important;
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        box-shadow: none !important;
    }
    html body div[data-testid="stSelectbox"] div[role="group"]:hover,
    html body div[data-testid="stSelectbox"] [data-rac][role="group"]:hover,
    html body div[data-testid="stSelectbox"] div[role="group"]:focus-within,
    html body div[data-testid="stSelectbox"] [data-rac][role="group"]:focus-within,
    html body [data-baseweb="select"] > div:hover,
    html body div[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {
        border-color: var(--header-border-left) !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.2) !important;
    }
    html body div[data-testid="stSelectbox"] input,
    html body div[data-testid="stSelectbox"] input[role="combobox"],
    html body div[data-testid="stSelectbox"] [data-rac] input,
    html body div[data-testid="stSelectbox"] div[role="group"] input,
    html body [data-baseweb="select"] input,
    html body [data-baseweb="select"] span,
    html body [data-baseweb="select"] div,
    html body div[data-testid="stSelectbox"] [data-baseweb="select"] input,
    html body div[data-testid="stSelectbox"] [data-baseweb="select"] span,
    html body div[data-testid="stSelectbox"] [data-baseweb="select"] div {
        background: transparent !important;
        background-color: transparent !important;
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }
    html body div[data-testid="stSelectbox"] button,
    html body div[data-testid="stSelectbox"] button[data-rac],
    html body div[data-testid="stSelectbox"] [data-rac] button {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        color: var(--input-text) !important;
    }
    html body div[data-testid="stSelectbox"] svg,
    html body div[data-testid="stSelectbox"] button svg,
    html body [data-baseweb="select"] svg {
        fill: var(--input-text) !important;
        stroke: var(--input-text) !important;
        color: var(--input-text) !important;
        background: transparent !important;
        background-color: transparent !important;
    }
    
    /* Popovers, Menus, Dropdown Options (React-Aria & BaseWeb) */
    html body div.react-aria-Popover,
    html body [data-rac].react-aria-Popover,
    html body div[data-rac][role="listbox"],
    html body div[role="listbox"],
    html body [data-baseweb="popover"],
    html body [data-baseweb="popover"] > div,
    html body [data-baseweb="popover"] ul,
    html body [data-baseweb="menu"],
    html body [data-baseweb="menu"] ul,
    html body ul[role="listbox"],
    html body ul[data-testid="stSelectboxVirtualDropdown"] {
        background: var(--input-bg) !important;
        background-color: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25) !important;
        padding: 4px !important;
    }
    html body div[data-rac][role="option"],
    html body div.react-aria-ListBoxItem,
    html body div[role="option"],
    html body li[role="option"],
    html body [data-baseweb="popover"] li,
    html body [data-baseweb="menu"] li {
        background: var(--input-bg) !important;
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        -webkit-text-fill-color: var(--input-text) !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        border-radius: 4px !important;
        margin-bottom: 2px !important;
        padding: 8px 12px !important;
        transition: all 0.15s ease !important;
        cursor: pointer !important;
    }
    html body div[data-rac][role="option"]:hover,
    html body div[data-rac][role="option"][aria-selected="true"],
    html body div[data-rac][role="option"][data-focused="true"],
    html body div[data-rac][role="option"][data-selected="true"],
    html body div.react-aria-ListBoxItem:hover,
    html body div.react-aria-ListBoxItem[data-selected="true"],
    html body div.react-aria-ListBoxItem[data-focused="true"],
    html body div[role="option"]:hover,
    html body div[role="option"][aria-selected="true"],
    html body li[role="option"]:hover,
    html body li[role="option"][aria-selected="true"],
    html body [data-baseweb="popover"] li:hover,
    html body [data-baseweb="menu"] li:hover {
        background: var(--card-hover-bg) !important;
        background-color: var(--card-hover-bg) !important;
        color: var(--header-border-left) !important;
        -webkit-text-fill-color: var(--header-border-left) !important;
    }

    /* Top Header Row Layout & Symmetrical Cards */
    .block-container > div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:first-of-type {
        margin-bottom: 0 !important;
        align-items: stretch !important;
    }
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Top Right Action Card (Backend Status & Dark Mode Toggle) - Scoped exclusively to action column */
    div[data-testid="stColumn"]:has(#header-control-card-anchor) > div[data-testid="stVerticalBlock"],
    div[data-testid="stColumn"]:has(#header-control-card-anchor) {
        background: var(--header-bg) !important;
        border: 1px solid var(--header-border) !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: var(--header-shadow) !important;
        height: 100% !important;
        min-height: 68px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-sizing: border-box !important;
        margin-bottom: 0 !important;
        gap: 4px !important;
    }
    div[data-testid="stColumn"]:has(#header-control-card-anchor) div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stColumn"]:has(#header-control-card-anchor) div[data-testid="stMarkdownContainer"] > p {
        margin: 0 !important;
    }

    /* Header Theme Toggle Capsule & Distinct Badge Styling */
    .st-key-theme_toggle,
    div[data-testid="stColumn"]:has(#header-control-card-anchor) div[data-testid="stToggle"],
    div[data-testid="stColumn"]:has(#header-control-card-anchor) div.stCheckbox {
        margin: 0 !important;
        margin-top: 4px !important;
        padding: 0 !important;
        width: 100% !important;
    }
    .st-key-theme_toggle [data-testid="stCheckbox"],
    .st-key-theme_toggle div[data-testid="stCheckbox"],
    .st-key-theme_toggle [data-testid="stToggle"],
    .st-key-theme_toggle div[data-testid="stToggle"] {
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }
    .st-key-theme_toggle label {
        display: flex !important;
        flex-direction: row-reverse !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        cursor: pointer !important;
        user-select: none !important;
        margin: 0 !important;
        padding: 5px 10px !important;
        background: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: 6px !important;
        box-sizing: border-box !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .st-key-theme_toggle label:hover {
        border-color: var(--header-border-left) !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.22) !important;
    }
    .st-key-theme_toggle label div[data-testid="stMarkdownContainer"],
    .st-key-theme_toggle [data-testid="stMarkdownContainer"] {
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .st-key-theme_toggle label div[data-testid="stMarkdownContainer"] p,
    .st-key-theme_toggle [data-testid="stMarkdownContainer"] p {
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.70rem !important;
        font-weight: 800 !important;
        color: var(--text-primary) !important;
        letter-spacing: 0.07em !important;
        text-transform: uppercase !important;
        margin: 0 !important;
        padding: 3px 8px !important;
        border-radius: 4px !important;
        background: rgba(148, 163, 184, 0.12) !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        line-height: 1.2 !important;
    }
    /* Explicit high-contrast toggle switch track and border across all Streamlit DOM variants */
    .st-key-theme_toggle [data-testid="stCheckbox"] label > div:first-of-type,
    .st-key-theme_toggle [data-testid="stCheckbox"] span + div,
    .st-key-theme_toggle [role="switch"],
    .st-key-theme_toggle div[data-testid="stCheckboxToggle"] > div,
    .st-key-theme_toggle span[data-baseweb="toggle"] {
        background-color: var(--toggle-track-bg) !important;
        border: 1.5px solid var(--toggle-track-border) !important;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.2s ease !important;
    }
    .st-key-theme_toggle [data-testid="stCheckbox"]:has(input:checked) label > div:first-of-type,
    .st-key-theme_toggle [data-testid="stCheckbox"]:has(input:checked) span + div,
    .st-key-theme_toggle [role="switch"][aria-checked="true"],
    .st-key-theme_toggle [role="switch"][data-checked="true"] {
        background-color: var(--header-border-left) !important;
        border-color: var(--header-border-left) !important;
    }
    .st-key-theme_toggle [data-testid="stCheckbox"] label > div:first-of-type > div,
    .st-key-theme_toggle [data-testid="stCheckbox"] span + div > div,
    .st-key-theme_toggle [role="switch"] > div {
        background-color: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25) !important;
    }

    /* Segmented Control & Pills Styling */
    div[data-testid="stSegmentedControl"],
    div[data-testid="stPills"] {
        gap: 4px !important;
        align-items: center !important;
    }
    div[data-testid="stSegmentedControl"] button,
    div[data-testid="stPills"] button {
        background: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        color: var(--text-secondary) !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.74rem !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"],
    div[data-testid="stSegmentedControl"] button[data-checked="true"],
    div[data-testid="stPills"] button[aria-checked="true"],
    div[data-testid="stPills"] button[data-checked="true"] {
        background: var(--action-btn-bg) !important;
        border-color: var(--header-border-left) !important;
        color: var(--header-border-left) !important;
        font-weight: 700 !important;
    }
    
    /* Popover button styling - Ensure high contrast across both themes */
    div[data-testid="stPopover"] button[data-testid="stPopoverButton"],
    div[data-testid="stPopover"] > button,
    div[data-testid="stPopover"] button,
    .stPopover button {
        background: var(--input-bg) !important;
        background-color: var(--input-bg) !important;
        border: 1px solid var(--input-border) !important;
        color: var(--text-primary) !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        height: 38px !important;
        padding: 0 12px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stPopover"] button *,
    .stPopover button * {
        color: var(--text-primary) !important;
        fill: var(--text-primary) !important;
    }
    div[data-testid="stPopover"] button:hover,
    .stPopover button:hover {
        border-color: var(--header-border-left) !important;
        color: var(--header-border-left) !important;
    }

    /* Automated Horizontal Scrolling Ticker for USP Description */
    @keyframes uspTicker {
        0% { transform: translateX(0); }
        100% { transform: translateX(-50%); }
    }
    details.usp-collapsible {
        background: var(--edge-bg) !important;
        border: 1px solid var(--edge-border) !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
        overflow: hidden !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--card-shadow) !important;
    }
    details.usp-collapsible summary.usp-summary {
        list-style: none !important;
        cursor: pointer !important;
        padding: 8px 14px !important;
        user-select: none !important;
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    details.usp-collapsible summary.usp-summary::-webkit-details-marker,
    details.usp-collapsible summary.usp-summary::marker {
        display: none !important;
    }
    .usp-summary-inner {
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
        overflow: hidden;
    }
    .usp-badge {
        background: rgba(56, 189, 248, 0.15);
        border: 1px solid rgba(56, 189, 248, 0.35);
        color: var(--header-border-left);
        font-family: 'Montserrat', sans-serif;
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        padding: 3px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        flex-shrink: 0;
    }
    .usp-ticker-wrap {
        overflow: hidden;
        white-space: nowrap;
        position: relative;
        flex: 1 1 auto;
        mask-image: linear-gradient(to right, transparent, black 3%, black 97%, transparent);
        -webkit-mask-image: linear-gradient(to right, transparent, black 3%, black 97%, transparent);
    }
    .usp-ticker-track {
        display: inline-flex;
        align-items: center;
        gap: 20px;
        animation: uspTicker 32s linear infinite;
        white-space: nowrap;
    }
    .usp-ticker-track:hover {
        animation-play-state: paused;
    }
    .usp-ticker-item {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: 0.80rem;
        color: var(--edge-text);
    }
    .usp-expand-btn {
        background: rgba(148, 163, 184, 0.12);
        border: 1px solid rgba(148, 163, 184, 0.3);
        color: var(--text-secondary);
        font-family: 'Montserrat', sans-serif;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        flex-shrink: 0;
        transition: all 0.2s ease;
    }
    details.usp-collapsible summary.usp-summary:hover .usp-expand-btn {
        background: rgba(59, 130, 246, 0.18);
        border-color: rgba(59, 130, 246, 0.4);
        color: #3b82f6;
    }
    details.usp-collapsible .usp-collapse-text { display: none; }
    details.usp-collapsible[open] .usp-expand-text { display: none; }
    details.usp-collapsible[open] .usp-collapse-text { display: inline; }
    details.usp-collapsible[open] summary.usp-summary {
        border-bottom: 1px solid var(--edge-border) !important;
    }
    .usp-content {
        padding: 12px 16px !important;
    }

    /* Live Intelligence Feed Header Right-Alignment & Distinct Sentiment Color Pills */
    .st-key-feed_sentiment_pills,
    .st-key-feed_sentiment_pills > div {
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
        width: 100% !important;
        margin-left: auto !important;
    }
    .st-key-feed_sentiment_pills div[data-testid="stPills"],
    .st-key-feed_sentiment_pills div[data-testid="stSegmentedControl"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"],
    .st-key-feed_sentiment_pills div[role="radiogroup"] {
        display: flex !important;
        justify-content: flex-end !important;
        margin-left: auto !important;
        width: auto !important;
        gap: 6px !important;
    }
    .st-key-feed_sentiment_pills [data-testid="stPills"] button,
    .st-key-feed_sentiment_pills div[role="radiogroup"] > button,
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li button {
        border-radius: 6px !important;
        font-family: 'Montserrat', sans-serif !important;
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        padding: 4px 12px !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        letter-spacing: 0.02em !important;
    }
    /* 1. All Button (Blue Accent) */
    .st-key-feed_sentiment_pills button:nth-of-type(1),
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1),
    .st-key-feed_sentiment_pills div[role="radiogroup"] > button:nth-of-type(1),
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button {
        border: 1px solid rgba(59, 130, 246, 0.4) !important;
        color: var(--text-primary) !important;
        background: var(--input-bg) !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(1):hover,
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1):hover,
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button:hover {
        border-color: #3b82f6 !important;
        background: rgba(59, 130, 246, 0.12) !important;
        color: #60a5fa !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(1)[aria-checked="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(1)[data-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1)[aria-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1)[data-checked="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button[aria-checked="true"] {
        background: rgba(59, 130, 246, 0.25) !important;
        border-color: #3b82f6 !important;
        color: #60a5fa !important;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.35) !important;
    }
    /* 2. Bullish Button (Emerald Green Accent) */
    .st-key-feed_sentiment_pills button:nth-of-type(2),
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2),
    .st-key-feed_sentiment_pills div[role="radiogroup"] > button:nth-of-type(2),
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(2) button {
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
        color: #10b981 !important;
        background: rgba(16, 185, 129, 0.08) !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(2):hover,
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2):hover,
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(2) button:hover {
        border-color: #10b981 !important;
        background: rgba(16, 185, 129, 0.16) !important;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.25) !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(2)[aria-checked="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(2)[data-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2)[aria-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2)[data-checked="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(2) button[aria-checked="true"] {
        background: rgba(16, 185, 129, 0.28) !important;
        border-color: #10b981 !important;
        color: #34d399 !important;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.4) !important;
    }
    /* 3. Bearish Button (Crimson Red Accent) */
    .st-key-feed_sentiment_pills button:nth-of-type(3),
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3),
    .st-key-feed_sentiment_pills div[role="radiogroup"] > button:nth-of-type(3),
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(3) button {
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
        color: #f87171 !important;
        background: rgba(239, 68, 68, 0.08) !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(3):hover,
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3):hover,
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(3) button:hover {
        border-color: #ef4444 !important;
        background: rgba(239, 68, 68, 0.16) !important;
        box-shadow: 0 0 8px rgba(239, 68, 68, 0.25) !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(3)[aria-checked="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(3)[data-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3)[aria-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3)[data-checked="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(3) button[aria-checked="true"] {
        background: rgba(239, 68, 68, 0.28) !important;
        border-color: #ef4444 !important;
        color: #f87171 !important;
        box-shadow: 0 0 12px rgba(239, 68, 68, 0.4) !important;
    }
    /* 4. Neutral Button (Slate Gray Accent) */
    .st-key-feed_sentiment_pills button:nth-of-type(4),
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4),
    .st-key-feed_sentiment_pills div[role="radiogroup"] > button:nth-of-type(4),
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(4) button {
        border: 1px solid rgba(148, 163, 184, 0.4) !important;
        color: var(--text-muted) !important;
        background: rgba(148, 163, 184, 0.08) !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(4):hover,
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4):hover,
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(4) button:hover {
        border-color: #94a3b8 !important;
        background: rgba(148, 163, 184, 0.16) !important;
        color: var(--text-primary) !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(4)[aria-checked="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(4)[data-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4)[aria-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4)[data-checked="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(4) button[aria-checked="true"] {
        background: rgba(148, 163, 184, 0.25) !important;
        border-color: #94a3b8 !important;
        color: #cbd5e1 !important;
        box-shadow: 0 0 10px rgba(148, 163, 184, 0.25) !important;
    }
    
    /* Dedicated Mini Index Grid & Card Styling */
    .mini-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 10px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--card-border);
    }
    .mini-index-card {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 8px;
        padding: 10px 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-sizing: border-box;
        box-shadow: var(--card-shadow);
    }
    .mini-index-card:hover {
        background: var(--card-hover-bg) !important;
        border-color: var(--card-hover-border) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Metrics & Institutional Typography */
    .metric-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
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
    .metric-hero {
        font-size: 2.35rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }
    .metric-sub {
        font-size: 0.84rem;
        font-weight: 500;
        color: var(--text-secondary) !important;
    }
    .green { color: var(--metric-green) !important; }
    .red { color: var(--metric-red) !important; } 
    .gray { color: var(--text-muted) !important; }
    
    .metric-footer {
        font-size: 0.82rem;
        color: var(--text-secondary) !important;
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
        .metric-title { font-size: 0.72rem; }
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
    .news-feed-scroll {
        background: transparent !important;
        border: none !important;
        padding: 4px 0 0 0;
        max-height: 480px;
        overflow-y: auto;
    }
    .news-feed-scroll::-webkit-scrollbar {
        width: 6px;
    }
    .news-feed-scroll::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.04);
        border-radius: 4px;
    }
    .news-feed-scroll::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.35);
        border-radius: 4px;
    }
    .news-feed-scroll::-webkit-scrollbar-thumb:hover {
        background: rgba(148, 163, 184, 0.55);
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
        border-color: rgba(59, 130, 246, 0.3) !important;
        transform: translateY(-1px);
    }
    .news-item-card:last-child {
        margin-bottom: 0;
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
    latest_ts = df_signals['timestamp'].max() if not df_signals.empty else None
    time_display_str = "14:05 IST"
    if pd.notna(latest_ts):
        try:
            ts_local = latest_ts.tz_convert('Asia/Kolkata') if latest_ts.tzinfo else latest_ts
            time_display_str = ts_local.strftime('%H:%M IST')
        except Exception:
            time_display_str = "LIVE"

    # --- Top Row: Header Banner (Left) & Top-Right Control Card (System Status + Theme Toggle) ---
    header_col, action_col = st.columns([0.72, 0.28])
    
    with header_col:
        st.markdown(f"""
        <div style="background: var(--header-bg); border: 1px solid var(--header-border); border-radius: 8px; padding: clamp(10px, 2vw, 14px) clamp(12px, 2.5vw, 20px); height: 100%; display: flex; align-items: center; backdrop-filter: blur(10px); box-shadow: var(--header-shadow); margin-bottom: 0; box-sizing: border-box;">
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
        <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
            <div style="display: inline-flex; align-items: center; gap: 5px; background: {'rgba(2, 132, 199, 0.10)' if is_light else 'rgba(56, 189, 248, 0.12)'}; border: 1px solid {'rgba(2, 132, 199, 0.28)' if is_light else 'rgba(56, 189, 248, 0.28)'}; padding: 3px 8px; border-radius: 4px;">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="{'#0284c7' if is_light else '#38bdf8'}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span style="font-size: 0.68rem; font-weight: 700; color: {'#0284c7' if is_light else '#38bdf8'}; font-family: 'Montserrat', sans-serif; letter-spacing: 0.04em; text-transform: uppercase;">UPDATED {time_display_str}</span>
            </div>
            <div style="display: inline-flex; align-items: center; gap: 6px; background: {status_bg}; border: 1px solid {status_border}; color: {status_text}; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.08em; padding: 3px 9px; border-radius: 4px; text-transform: uppercase; font-family: 'Montserrat', sans-serif; box-shadow: 0 0 10px rgba(16, 185, 129, 0.15);">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981; display: inline-block;"></span>
                SYSTEM ONLINE
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.toggle("🌙 Dark Mode" if is_dark else "☀️ Light Mode", key="theme_toggle")
    
    st.markdown(f"""
    <details class="usp-collapsible">
        <summary class="usp-summary">
            <div class="usp-summary-inner">
                <span class="usp-badge">⚡ QUANTITATIVE EDGE</span>
                <div class="usp-ticker-wrap">
                    <div class="usp-ticker-track">
                        <span class="usp-ticker-item"><strong>Pure Mathematical Sentiment</strong> via System-One CLM-8B</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: {'#059669' if is_light else '#34d399'};">🎯 Zero Hallucination:</strong> Native Choice Probabilities P(Bullish), P(Bearish), P(Neutral)</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: {'#7c3aed' if is_light else '#a78bfa'};">⚖️ OKF-Conditioned:</strong> Regional Macroeconomic Policy Rules Applied in Real-Time</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: {'#d97706' if is_light else '#fbbf24'};">📈 Momentum Vectors:</strong> 4P EMA Cross-Sectional Tracking</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: {'#0284c7' if is_light else '#38bdf8'};">🛡️ System Online:</strong> Institutional Ingestion & Execution Engine</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <!-- Infinite loop seamless duplicate -->
                        <span class="usp-ticker-item"><strong>Pure Mathematical Sentiment</strong> via System-One CLM-8B</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: {'#059669' if is_light else '#34d399'};">🎯 Zero Hallucination:</strong> Native Choice Probabilities P(Bullish), P(Bearish), P(Neutral)</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: {'#7c3aed' if is_light else '#a78bfa'};">⚖️ OKF-Conditioned:</strong> Regional Macroeconomic Policy Rules Applied in Real-Time</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: {'#d97706' if is_light else '#fbbf24'};">📈 Momentum Vectors:</strong> 4P EMA Cross-Sectional Tracking</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: {'#0284c7' if is_light else '#38bdf8'};">🛡️ System Online:</strong> Institutional Ingestion & Execution Engine</span>
                    </div>
                </div>
                <div class="usp-expand-btn">
                    <span class="usp-expand-text">DETAILS ▾</span>
                    <span class="usp-collapse-text">COLLAPSE ▴</span>
                </div>
            </div>
        </summary>
        <div class="usp-content">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <span style="font-family: 'Montserrat', sans-serif; font-size: clamp(0.85rem, 1.8vw, 0.98rem); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em;">Pure Mathematical Sentiment via Contrastive Language Modeling</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                    <span style="font-size: 0.65rem; font-weight: 700; color: {'#059669' if is_light else '#34d399'}; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">DETERMINISTIC</span>
                    <span style="font-size: 0.65rem; font-weight: 700; color: {'#7c3aed' if is_light else '#a78bfa'}; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">OKF-CONDITIONED</span>
                    <span style="font-size: 0.65rem; font-weight: 700; color: {'#d97706' if is_light else '#fbbf24'}; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">ZERO HALLUCINATION</span>
                </div>
            </div>
            <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: clamp(0.78rem, 1.5vw, 0.83rem); color: var(--edge-text); line-height: 1.6; margin-bottom: 0;">
                Generative LLMs suffer from prompt drift, hallucination, and confidence clustering. GSP replaces text generation with a <strong>System-One Contrastive Model (CLM-8B)</strong> that projects global news directly onto native choice probabilities: <strong style="color: {'#059669' if is_light else '#34d399'}; font-weight: 700;">P(Bullish)</strong>, <strong style="color: {'#dc2626' if is_light else '#f87171'}; font-weight: 700;">P(Bearish)</strong>, and <strong style="color: var(--text-muted); font-weight: 700;">P(Neutral)</strong>. Headlines are conditioned against regional macroeconomic policy rules (OKF), converting real-time global news into an institutional momentum score [-100, +100].
            </div>
        </div>
    </details>
    """, unsafe_allow_html=True)
    
    # Helper for segmented filter buttons (resilient across Streamlit versions)
    def render_segmented_filter(label, options, default_ix: int | None = 0, key=None):
        default_val = options[default_ix] if (default_ix is not None and 0 <= default_ix < len(options)) else None
        if hasattr(st, "pills"):
            res = st.pills(label, options, default=default_val, key=key, label_visibility="collapsed")
            return res
        elif hasattr(st, "segmented_control"):
            res = st.segmented_control(label, options, default=default_val, key=key, label_visibility="collapsed")
            return res
        else:
            return st.radio(label, options, index=default_ix, key=key, horizontal=True, label_visibility="collapsed")

    # --- Top Row: Filter Toolbar Card (5 Aligned Controls in 1 Single Line) ---
    with st.container(border=True):
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([1.1, 1.25, 1.35, 1.35, 1.05], gap="small")
        lbl_color = "#475569" if is_light else "#94a3b8"
        
        with filter_col1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 2px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{lbl_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span style="font-size: 0.70rem; font-weight: 700; color: {lbl_color}; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Montserrat', sans-serif;">TIMEFRAME</span>
            </div>
            """, unsafe_allow_html=True)
            timeframe_options = ["7 Days", "1 Day", "12 Hours", "6 Hours", "4 Hours", "1 Month", "1 Year", "All"]
            default_tf_ix = 0
            date_range = st.selectbox("Timeframe", timeframe_options, index=default_tf_ix, label_visibility="collapsed")
            
        with filter_col2:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 2px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{lbl_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                <span style="font-size: 0.70rem; font-weight: 700; color: {lbl_color}; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Montserrat', sans-serif;">REGION</span>
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
            
            region_name_map = {
                "IN": "India (IN)",
                "US": "United States (US)",
                "UK": "United Kingdom (UK)",
                "JP": "Japan (JP)"
            }
            display_regions = [region_name_map.get(r, r) for r in regions]
            default_reg_name = region_name_map.get("IN", "IN")
            default_ix = display_regions.index(default_reg_name) if default_reg_name in display_regions else 0
            selected_region_display = st.selectbox("Region", display_regions, index=default_ix, label_visibility="collapsed")
            selected_region = next((code for code, name in region_name_map.items() if name == selected_region_display), selected_region_display)

        with filter_col3:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 2px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{lbl_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                <span style="font-size: 0.70rem; font-weight: 700; color: {lbl_color}; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Montserrat', sans-serif;">CHART DISPLAY</span>
            </div>
            """, unsafe_allow_html=True)
            active_indices = df_signals[df_signals['market_region'] == selected_region]['index_ticker'].unique().tolist()
            active_indices = [x for x in active_indices if x != 'UNKNOWN']
            chart_display = st.selectbox("Chart Display", ["All Indices"] + active_indices, index=0, label_visibility="collapsed")

        with filter_col4:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 2px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{lbl_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 10"></polyline></svg>
                <span style="font-size: 0.70rem; font-weight: 700; color: {lbl_color}; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Montserrat', sans-serif;">TIMEZONE</span>
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
            display_tz = st.selectbox("Timezone", tz_keys, index=default_tz_ix, label_visibility="collapsed")
            target_tz = tz_options[display_tz]
            tz_abbr = display_tz.split('(')[-1].replace(')', '').strip() if '(' in display_tz else display_tz

        with filter_col5:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 2px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{lbl_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                <span style="font-size: 0.70rem; font-weight: 700; color: {lbl_color}; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Montserrat', sans-serif;">EMA WINDOW</span>
            </div>
            """, unsafe_allow_html=True)
            ema_display_options = ["4 Periods", "8 Periods", "12 Periods", "24 Periods"]
            selected_ema_label = st.selectbox("EMA Window", ema_display_options, index=0, label_visibility="collapsed")
            ema_window = int(selected_ema_label.split()[0])

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
        cutoff = now  # default: no filtering if date_range is unrecognized
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
        
        # Ensure plot timestamps are naive in target_tz so Plotly renders exact wall-clock time
        plot_trend_x = df_trend['timestamp'].dt.tz_localize(None) if df_trend['timestamp'].dt.tz is not None else df_trend['timestamp']
        
        # --- Main Layout Split (1 Narrow Left, 1 Wide Right) ---
        left_col, right_col = st.columns([1.2, 4])
        
        with left_col:
            # 1. Delta calculation and direction-accurate labeling
            if abs(delta) < 0.05:
                delta_str = "— No change"
                delta_pill_color = "#475569" if is_light else "#94a3b8"
                delta_pill_bg = "rgba(148, 163, 184, 0.12)" if is_light else "rgba(148, 163, 184, 0.15)"
                delta_pill_border = "rgba(148, 163, 184, 0.3)"
            elif delta > 0:
                delta_str = f"▲ +{abs(delta):.1f}% change"
                delta_pill_color = "#059669" if is_light else "#34d399"
                delta_pill_bg = "rgba(16, 185, 129, 0.12)" if is_light else "rgba(16, 185, 129, 0.15)"
                delta_pill_border = "rgba(16, 185, 129, 0.3)"
            else:
                delta_str = f"▼ -{abs(delta):.1f}% change"
                delta_pill_color = "#dc2626" if is_light else "#f87171"
                delta_pill_bg = "rgba(239, 68, 68, 0.12)" if is_light else "rgba(239, 68, 68, 0.15)"
                delta_pill_border = "rgba(239, 68, 68, 0.3)"
                
            val_color = "green" if current_ema > 0 else "red" if current_ema < 0 else ""
            
            # 2. Market Bias Regime
            bias = "Bullish" if current_ema > 5 else "Bearish" if current_ema < -5 else "Neutral"
            if bias == "Bullish":
                b_color_hex = "#059669" if is_light else "#34d399"
                b_pill_bg = "rgba(16, 185, 129, 0.12)" if is_light else "rgba(16, 185, 129, 0.15)"
                b_pill_border = "rgba(16, 185, 129, 0.3)"
                b_val_color = "green"
            elif bias == "Bearish":
                b_color_hex = "#dc2626" if is_light else "#f87171"
                b_pill_bg = "rgba(239, 68, 68, 0.12)" if is_light else "rgba(239, 68, 68, 0.15)"
                b_pill_border = "rgba(239, 68, 68, 0.3)"
                b_val_color = "red"
            else:
                b_color_hex = "#7c3aed" if is_light else "#c084fc"
                b_pill_bg = "rgba(124, 58, 237, 0.12)" if is_light else "rgba(168, 85, 247, 0.15)"
                b_pill_border = "rgba(124, 58, 237, 0.3)" if is_light else "rgba(168, 85, 247, 0.3)"
                b_val_color = ""

            # 3. Telemetry metrics
            total_news_count = len(filtered_signals)
            tracked_count = filtered_signals['index_ticker'].nunique()
            
            nv_color = "#0284c7" if is_light else "#38bdf8"
            nv_bg = "rgba(2, 132, 199, 0.12)" if is_light else "rgba(56, 189, 248, 0.12)"
            nv_border = "rgba(2, 132, 199, 0.3)" if is_light else "rgba(56, 189, 248, 0.3)"
            
            ti_color = "#059669" if is_light else "#34d399"

            # Render Left Column (4 Symmetrically Stacked KPI Cards)
            kpi_column_html = (
                '<div class="kpi-column-container">'
                # Card 1: Headline Hero Metric (Aggregate Optimism)
                '<div class="white-card kpi-card">'
                '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 2px;">'
                '<span class="metric-title" style="margin-bottom: 0;">Aggregate Optimism</span>'
                f'<span style="font-size: 0.72rem; font-weight: 700; color: var(--header-border-left); text-transform: uppercase; font-family: \'Montserrat\', sans-serif;">{selected_region}</span>'
                '</div>'
                f'<div class="metric-value metric-hero {val_color}">{current_ema:+.1f}</div>'
                '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 2px;">'
                f'<span style="font-size: 0.74rem; font-weight: 700; color: {delta_pill_color}; background: {delta_pill_bg}; border: 1px solid {delta_pill_border}; padding: 2px 7px; border-radius: 4px; font-family: \'Montserrat\', sans-serif;">{delta_str}</span>'
                f'<span style="font-size: 0.78rem; color: var(--text-secondary);">vs previous period</span>'
                '</div>'
                '<div class="metric-footer" style="margin-top: 6px; padding-top: 6px; font-size: 0.78rem; color: var(--text-secondary); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">'
                '<span>Confidence vector</span>'
                '<span style="color: var(--text-primary); font-weight: 600;">System-One CLM</span>'
                '</div>'
                '</div>'

                # Card 2: Strategic Regime (Market Bias)
                '<div class="white-card kpi-card">'
                '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 2px;">'
                '<span class="metric-title" style="margin-bottom: 0;">Market Bias</span>'
                f'<span style="font-size: 0.68rem; font-weight: 800; color: {b_color_hex}; background: {b_pill_bg}; border: 1px solid {b_pill_border}; padding: 2px 7px; border-radius: 4px; text-transform: uppercase; font-family: \'Montserrat\', sans-serif; letter-spacing: 0.04em;">{bias}</span>'
                '</div>'
                f'<div class="metric-value {b_val_color}" style="font-size: 1.55rem;">{bias}</div>'
                '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 2px;">'
                f'<span style="font-size: 0.78rem; color: var(--text-secondary);">{ema_window}-period moving average</span>'
                '</div>'
                '<div class="metric-footer" style="margin-top: 6px; padding-top: 6px; font-size: 0.78rem; color: var(--text-secondary); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">'
                '<span>Signal strategy</span>'
                '<span style="color: var(--text-primary); font-weight: 600;">EMA Crossover</span>'
                '</div>'
                '</div>'

                # Card 3: Total News Volume
                '<div class="white-card kpi-card">'
                '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 2px;">'
                '<span class="metric-title" style="margin-bottom: 0;">Total News Volume</span>'
                f'<span style="font-size: 0.68rem; font-weight: 700; color: {nv_color}; background: {nv_bg}; border: 1px solid {nv_border}; padding: 2px 7px; border-radius: 4px; font-family: \'Montserrat\', sans-serif;">{date_range} Window</span>'
                '</div>'
                f'<div class="metric-value" style="color: var(--text-primary); font-size: 1.55rem;">{total_news_count}</div>'
                '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 2px;">'
                f'<span style="font-size: 0.78rem; color: var(--text-secondary);">articles ingested</span>'
                '</div>'
                '<div class="metric-footer" style="margin-top: 6px; padding-top: 6px; font-size: 0.78rem; color: var(--text-secondary); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">'
                '<span>Ingestion cadence</span>'
                '<span style="color: var(--text-primary); font-weight: 600;">Every 2 hours</span>'
                '</div>'
                '</div>'

                # Card 4: Tracked Indices
                '<div class="white-card kpi-card">'
                '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 2px;">'
                '<span class="metric-title" style="margin-bottom: 0;">Tracked Indices</span>'
                f'<span style="font-size: 0.68rem; font-weight: 700; color: {ti_color}; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 2px 7px; border-radius: 4px; text-transform: uppercase; font-family: \'Montserrat\', sans-serif;">{selected_region}</span>'
                '</div>'
                f'<div class="metric-value" style="color: var(--text-primary); font-size: 1.55rem;">{tracked_count}</div>'
                '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 2px;">'
                f'<span style="font-size: 0.74rem; font-weight: 700; color: {ti_color}; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 2px 6px; border-radius: 4px; font-family: \'Montserrat\', sans-serif;">100% Active</span>'
                f'<span style="font-size: 0.78rem; color: var(--text-secondary);">real-time monitored</span>'
                '</div>'
                '<div class="metric-footer" style="margin-top: 6px; padding-top: 6px; font-size: 0.78rem; color: var(--text-secondary); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">'
                '<span>Active universe</span>'
                '<span style="color: var(--text-primary); font-weight: 600;">20 Global Assets</span>'
                '</div>'
                '</div>'
                '</div>'
            )
            st.markdown(kpi_column_html, unsafe_allow_html=True)

        with right_col:
            # --- Combined Chart & Mini Index Container (unified alignment & borders) ---
            with st.container(border=True):
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border); margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.35); padding: 5px; border-radius: 6px; display: flex; align-items: center;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                        </div>
                        <div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); font-family: 'Montserrat', sans-serif;">Aggregate Market Optimism</div>
                            <div style="font-size: 0.78rem; color: var(--text-muted); font-family: 'IBM Plex Sans', sans-serif;">Multi-index sentiment surface & {selected_region} moving average</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.75rem; color: var(--text-muted); font-family: 'IBM Plex Sans', sans-serif;">Scale: [-100, +100] • {tz_abbr}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                fig_area = go.Figure()
                
                # Highly distinct, recognizable color palette with matching soft translucent fills
                distinct_colors = ["#0284c7", "#f59e0b", "#10b981", "#ec4899", "#8b5cf6", "#06b6d4"]
                fill_colors = [
                    "rgba(2, 132, 199, 0.20)",
                    "rgba(245, 158, 11, 0.20)",
                    "rgba(16, 185, 129, 0.20)",
                    "rgba(236, 72, 153, 0.20)",
                    "rgba(139, 92, 246, 0.20)",
                    "rgba(6, 182, 212, 0.20)"
                ]
                active_tickers = [c for c in filtered_signals['index_ticker'].unique() if c != 'UNKNOWN']
                
                # Plot individual index observations with translucent area fills
                for i, ticker in enumerate(active_tickers):
                    if chart_display != "All Indices" and ticker != chart_display:
                        continue
                    t_df = filtered_signals[filtered_signals['index_ticker'] == ticker].sort_values('timestamp')
                    if t_df.empty:
                        continue
                    t_grouped = t_df.groupby(pd.Grouper(key='timestamp', freq=freq_str))['sentiment_index'].mean().dropna().reset_index()
                    if t_grouped.empty:
                        continue
                    t_x = t_grouped['timestamp'].dt.tz_localize(None) if t_grouped['timestamp'].dt.tz is not None else t_grouped['timestamp']

                    fig_area.add_trace(go.Scatter(
                        x=t_x, y=t_grouped['sentiment_index'],
                        mode='lines+markers', name=ticker,
                        line=dict(width=1.8, color=distinct_colors[i % len(distinct_colors)]),
                        marker=dict(size=4),
                        fill='tozeroy',
                        fillcolor=fill_colors[i % len(fill_colors)],
                        opacity=0.9,
                        connectgaps=True
                    ))
                
                # Add bold prominent line for Global EMA Trend on top
                ema_color = '#0f172a' if is_light else '#f8fafc'
                fig_area.add_trace(go.Scatter(
                    x=plot_trend_x, y=df_trend['EMA_Index'],
                    mode='lines',
                    line=dict(color=ema_color, width=3.2, shape='linear'), 
                    name=f'{selected_region} Trend ({ema_window}P EMA)'
                ))
                
                fig_area.update_layout(
                    height=375, margin=dict(l=0, r=0, t=10, b=0),
                    plot_bgcolor="rgba(255,255,255,0.4)" if is_light else "rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        font=dict(color="#0f172a" if is_light else "#f8fafc", size=11, family="Montserrat")
                    ),
                    xaxis=dict(
                        showgrid=True, gridcolor='rgba(148, 163, 184, 0.22)' if is_light else 'rgba(255,255,255,0.06)',
                        showline=True, linecolor='rgba(100, 116, 139, 0.35)' if is_light else 'rgba(255,255,255,0.15)', linewidth=1,
                        ticks='outside', tickcolor='rgba(100, 116, 139, 0.35)' if is_light else 'rgba(255,255,255,0.25)', ticklen=4,
                        title=dict(text=f"<b>TIMELINE • {tz_abbr}</b>", font=dict(size=11, color="#0284c7" if is_light else "#38bdf8", family="Montserrat")),
                        tickfont=dict(size=10, color="#334155" if is_light else "#94a3b8", family="IBM Plex Sans")
                    ),
                    yaxis=dict(
                        range=[-105, 105],
                        dtick=25,
                        showgrid=True, gridcolor='rgba(148, 163, 184, 0.22)' if is_light else 'rgba(255,255,255,0.06)',
                        zeroline=True, zerolinecolor='rgba(148, 163, 184, 0.45)' if is_light else 'rgba(148, 163, 184, 0.35)', zerolinewidth=1.5,
                        showline=True, linecolor='rgba(100, 116, 139, 0.35)' if is_light else 'rgba(255,255,255,0.15)', linewidth=1,
                        ticks='outside', tickcolor='rgba(100, 116, 139, 0.35)' if is_light else 'rgba(255,255,255,0.25)', ticklen=4,
                        title=dict(text="<b>OPTIMISM SCORE</b>", font=dict(size=11, color="#0284c7" if is_light else "#38bdf8", family="Montserrat")),
                        tickfont=dict(size=10, color="#0f172a" if is_light else "#f8fafc", family="IBM Plex Sans"),
                        side="right"
                    )
                )
                st.plotly_chart(fig_area, use_container_width=True, config={'displayModeBar': 'hover', 'scrollZoom': True, 'displaylogo': False})

                # --- Mini KPI Tiles for Individual Indices (Inside same container for flush borders) ---
                valid_tickers = [t for t in active_tickers if t != 'UNKNOWN']
                if valid_tickers:
                    kpi_html = '<div class="mini-kpi-grid">'
                    
                    for ticker in valid_tickers:
                        t_sub = filtered_signals[filtered_signals['index_ticker'] == ticker].sort_values('timestamp')
                        t_grp = t_sub.groupby(pd.Grouper(key='timestamp', freq=freq_str))['sentiment_index'].mean().dropna()
                        latest_score = t_grp.iloc[-1] if len(t_grp) > 0 else 0
                        prev_score = t_grp.iloc[-2] if len(t_grp) > 1 else latest_score
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
                        
                        if abs(delta_idx) < 0.05:
                            delta_tag = '<span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">— No change</span>'
                        elif delta_idx > 0:
                            delta_tag = f'<span style="font-size: 0.75rem; font-weight: 700; color: #059669; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 1px 6px; border-radius: 4px; font-family: \'Montserrat\', sans-serif;">▲ {abs(delta_idx):.1f}%</span> <span style="font-size: 0.75rem; color: var(--text-secondary);">momentum</span>'
                        else:
                            delta_tag = f'<span style="font-size: 0.75rem; font-weight: 700; color: #dc2626; background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.25); padding: 1px 6px; border-radius: 4px; font-family: \'Montserrat\', sans-serif;">▼ {abs(delta_idx):.1f}%</span> <span style="font-size: 0.75rem; color: var(--text-secondary);">momentum</span>'
                        
                        kpi_html += (
                            f'<div class="mini-index-card" style="border-left: 3px solid {t_card_border}; margin-bottom: 0;">'
                            '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
                            f'<span style="font-family: \'Montserrat\', sans-serif; font-size: 0.78rem; font-weight: 700; color: {"#0f172a" if is_light else "#f8fafc"}; text-transform: uppercase; letter-spacing: 0.03em;">{ticker}</span>'
                            f'<span style="font-family: \'Montserrat\', sans-serif; font-size: 0.68rem; font-weight: 800; color: {t_status_color}; background: {t_status_bg}; border: 1px solid {t_status_border}; padding: 1px 6px; border-radius: 4px; letter-spacing: 0.04em;">{ticker_status}</span>'
                            '</div>'
                            f'<div style="font-family: \'Montserrat\', sans-serif; font-size: clamp(1.2rem, 2vw, 1.6rem); font-weight: 800; color: {t_val_color}; margin: 2px 0;">{latest_score:+.1f}</div>'
                            f'<div style="display: flex; align-items: center; gap: 5px; margin-top: 4px;">{delta_tag}</div>'
                            '</div>'
                        )
                    
                    kpi_html += '</div>'
                    st.markdown(kpi_html, unsafe_allow_html=True)

        # --- Regional News Feed at the Bottom (Isolated Fragment for Dynamic Rendering) ---
        if hasattr(st, "fragment"):
            fragment_decorator = st.fragment
        elif hasattr(st, "experimental_fragment"):
            fragment_decorator = st.experimental_fragment  # type: ignore[attr-defined]
        else:
            def fragment_decorator(func):
                return func

        @fragment_decorator
        def render_live_intelligence_feed(region_payloads, selected_region, is_light, date_range):
            total_events = len(region_payloads)
            bullish_count = int((region_payloads['sentiment_index'] >= 0.5).sum()) if not region_payloads.empty else 0
            bearish_count = int((region_payloads['sentiment_index'] <= -0.5).sum()) if not region_payloads.empty else 0
            neutral_count = total_events - bullish_count - bearish_count

            with st.container(border=True):
                feed_header_col1, feed_header_col2 = st.columns([0.42, 0.58], vertical_alignment="center")
                with feed_header_col1:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 8px; padding: 4px 0;">
                        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #3b82f6; box-shadow: 0 0 8px #3b82f6;"></span>
                        <span style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); font-family: 'Montserrat', sans-serif;">{selected_region} Live Intelligence Feed</span>
                    </div>
                    """, unsafe_allow_html=True)
                with feed_header_col2:
                    feed_pill_options = [
                        f"All {total_events}",
                        f"Bullish {bullish_count}",
                        f"Bearish {bearish_count}",
                        f"Neutral {neutral_count}"
                    ]
                    selected_feed_pill = render_segmented_filter("feed_filter", feed_pill_options, default_ix=None, key="feed_sentiment_pills")

                if selected_feed_pill is not None:
                    if "Bullish" in selected_feed_pill:
                        feed_display_payloads = region_payloads[region_payloads['sentiment_index'] >= 0.5]
                        sentiment_label = "Bullish"
                    elif "Bearish" in selected_feed_pill:
                        feed_display_payloads = region_payloads[region_payloads['sentiment_index'] <= -0.5]
                        sentiment_label = "Bearish"
                    elif "Neutral" in selected_feed_pill or "Noise" in selected_feed_pill:
                        feed_display_payloads = region_payloads[(region_payloads['sentiment_index'] > -0.5) & (region_payloads['sentiment_index'] < 0.5)]
                        sentiment_label = "Neutral"
                    else:
                        feed_display_payloads = region_payloads
                        sentiment_label = "All"

                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 4px 10px 4px; border-bottom: 1px solid var(--feed-card-border); margin-bottom: 10px;">
                        <span style="font-size: 0.78rem; font-weight: 700; color: var(--text-secondary); font-family: 'Montserrat', sans-serif; letter-spacing: 0.04em;">
                            STREAMING {len(feed_display_payloads)} {sentiment_label.upper()} HEADLINES
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Directly render top headlines in a scrollable feed container
                    html_feed = '<div class="news-feed-scroll">'
                    if not feed_display_payloads.empty:
                        for _, row in feed_display_payloads.iterrows():
                            sentiment = row['sentiment_index']
                            if date_range in ["4 Hours", "4 Hour", "4H", "6 Hours", "6 Hour", "6H", "12 Hours", "12 Hour", "12H", "1 Day", "1Day", "1D", "24 Hours", "24 Hour", "24H"]:
                                time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M')
                            else:
                                time_str = pd.to_datetime(row['timestamp']).strftime('%b %d, %H:%M')
                            ticker_label = row.get('index_ticker', 'Macro')
                            
                            parsed = clean_news_item(row['raw_text'])
                            clean_headline = parsed['headline']
                            source = parsed['source']
                            
                            # Determine Sentiment & Neutral status
                            if abs(sentiment) < 0.5:
                                status_badge = f'<span style="background: {"rgba(148, 163, 184, 0.2)" if is_light else "rgba(148, 163, 184, 0.18)"}; border: 1px solid {"rgba(148, 163, 184, 0.35)" if is_light else "rgba(148, 163, 184, 0.45)"}; color: {"#475569" if is_light else "#cbd5e1"}; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.06em; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">NEUTRAL</span>'
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
                        html_feed += f'<div style="color: var(--text-muted); font-size: 0.88rem; padding: 18px; text-align: center; font-family: \'IBM Plex Sans\', sans-serif;">No news events matching the selected sentiment filter for {selected_region}.</div>'

                    html_feed += '</div>'
                    st.markdown(html_feed, unsafe_allow_html=True)

        region_payloads = display_payloads[display_payloads['market_region'] == selected_region]
        if not region_payloads.empty:
            region_payloads = region_payloads.sort_values('timestamp', ascending=False)
        render_live_intelligence_feed(region_payloads, selected_region, is_light, date_range)
            

    else:
        st.warning("No data found for the selected parameters.")
else:
    st.info("Database empty. Run the ingestion engine to populate.")
