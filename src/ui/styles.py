"""
Permanent Dark Theme and Institutional UI Styling for Valence.
"""

import streamlit as st

# --- Permanent Dark Theme Enforcement ---
is_dark = True
is_light = False
st.session_state['theme_toggle'] = True

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
        --background-color: #08090d !important;
        --secondary-background-color: #0f1118 !important;
        --text-color: #f8fafc !important;
        --bg-main: #08090d;
        --bg-gradient: #08090d;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --card-bg: rgba(15, 17, 24, 0.75);
        --card-border: rgba(255, 255, 255, 0.08);
        --card-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        --card-hover-bg: rgba(22, 25, 36, 0.85);
        --card-hover-border: rgba(255, 255, 255, 0.16);
        --input-bg: #12141d;
        --input-border: rgba(255, 255, 255, 0.10);
        --input-text: #f8fafc;
        --header-bg: linear-gradient(135deg, rgba(15, 17, 24, 0.95) 0%, rgba(20, 24, 33, 0.7) 100%);
        --header-border: rgba(255, 255, 255, 0.10);
        --header-border-left: #10b981;
        --header-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        --edge-bg: rgba(15, 17, 24, 0.85);
        --edge-border: rgba(255, 255, 255, 0.08);
        --edge-accent: #10b981;
        --edge-text: #94a3b8;
        --feed-bg: rgba(15, 17, 24, 0.6);
        --feed-border: rgba(255, 255, 255, 0.08);
        --feed-card-bg: rgba(15, 17, 24, 0.75);
        --feed-card-border: rgba(255, 255, 255, 0.06);
        --feed-card-hover: rgba(22, 25, 36, 0.85);
        --feed-headline: #f8fafc;
        --feed-badge-bg: rgba(255, 255, 255, 0.04);
        --feed-badge-border: rgba(255, 255, 255, 0.08);
        --feed-badge-text: #94a3b8;
        --action-btn-bg: rgba(255, 255, 255, 0.05);
        --action-btn-border: rgba(255, 255, 255, 0.15);
        --action-btn-color: #f8fafc;
        --action-btn-hover-bg: rgba(16, 185, 129, 0.15);
        --action-btn-hover-border: #10b981;
        --action-btn-hover-color: #ffffff;
        --metric-green: #10b981;
        --metric-red: #f43f5e;
        --toggle-track-bg: #27272a;
        --toggle-track-border: #3f3f46;
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
    
    /* Master Vertical Rhythm: Deterministic 10px Spacing Between All Tiers Across Entire Dashboard */
    .block-container > div[data-testid="stVerticalBlock"],
    div[data-testid="stFragment"] > div[data-testid="stVerticalBlock"],
    div[data-testid="stFragment"] div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        gap: 10px !important;
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
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]),
    div[data-testid="stElementContainer"]:has(.kpi-column-container),
    div[data-testid="stElementContainer"]:has(div[data-testid="stPlotlyChart"]) {
        align-items: stretch !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) div[data-testid="stColumn"]:first-child,
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) div[data-testid="column"]:first-child {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) div[data-testid="stColumn"]:first-child > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) div[data-testid="column"]:first-child > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="column"] > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        flex: 1 1 auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) div[data-testid="stElementContainer"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) div[data-testid="element-container"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) .stMarkdown:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) div[data-testid="stMarkdown"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) div[data-testid="stMarkdownContainer"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) div[data-testid="stElementContainer"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) div[data-testid="element-container"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) .stMarkdown:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) div[data-testid="stMarkdown"]:has(.kpi-column-container),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) div[data-testid="stMarkdownContainer"]:has(.kpi-column-container),
    div:has(> .kpi-column-container),
    div:has(> div > .kpi-column-container),
    div:has(> div > div > .kpi-column-container) {
        height: 100% !important;
        flex: 1 1 auto !important;
        display: flex !important;
        flex-direction: column !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .kpi-column-container {
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        height: 100% !important;
        min-height: 100% !important;
        flex: 1 1 auto !important;
        gap: 8px !important;
        box-sizing: border-box !important;
    }
    .kpi-column-container .kpi-card {
        flex: 1 1 0px !important;
        margin-bottom: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        padding: 10px 12px !important;
        box-sizing: border-box !important;
    }
    .kpi-card-content {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    /* Right column chart & mini-kpi container: Symmetrical layout with left column */
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) {
        align-items: stretch !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        align-self: stretch !important;
        height: auto !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="stColumn"]:last-child > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="column"]:last-child > div[data-testid="stVerticalBlock"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"]:last-child div:has(> .st-key-market_optimism_chart_container),
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="stColumn"]:last-child div:has(> .st-key-market_optimism_chart_container),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="column"]:last-child div:has(> .st-key-market_optimism_chart_container),
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="column"]:last-child div:has(> .st-key-market_optimism_chart_container) {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        flex: 1 1 auto !important;
    }
    .st-key-market_optimism_chart_container,
    div[data-testid="stVerticalBlock"].st-key-market_optimism_chart_container,
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="stColumn"]:last-child div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]) > div[data-testid="column"]:last-child div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) > div[data-testid="column"]:last-child div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 8px !important;
        box-shadow: var(--card-shadow) !important;
        padding: 14px 18px 14px 18px !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        height: auto !important;
        min-height: 100% !important;
        flex: 1 1 auto !important;
        gap: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"]),
    div[data-testid="stHorizontalBlock"]:has(.kpi-column-container) {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stElementContainer"]:has(> div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"])),
    div[data-testid="element-container"]:has(> div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPlotlyChart"])) {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }


    /* Filter Toolbar Card Enclosure (Ultra-Compact, Identical Alignment Across All 5 Columns) */
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] div[data-testid="stSelectbox"]),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(div[data-testid="stSelectbox"]),
    div[data-testid="stElementContainer"]:has(div[data-testid="stSelectbox"]) > div[data-testid="stVerticalBlock"],
    div[data-testid="stElementContainer"]:has(div[data-testid="stSelectbox"]) {
        padding: 8px 14px 10px 14px !important;
        margin-top: 0 !important;
        margin-bottom: 10px !important;
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
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.2) !important;
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

    /* Top Header Banner Card (Unified Single-Enclosure Institutional Layout) */
    .header-banner-card {
        background: var(--header-bg);
        border: 1px solid var(--header-border);
        border-radius: 8px;
        padding: clamp(10px, 1.8vw, 14px) clamp(12px, 2vw, 18px);
        min-height: 64px;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-sizing: border-box;
        backdrop-filter: blur(10px);
        box-shadow: var(--header-shadow);
        transition: all 0.2s ease;
        margin-bottom: 10px !important;
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
        margin-top: 0 !important;
        margin-bottom: 10px !important;
        clear: both !important;
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
        background: rgba(16, 185, 129, 0.12);
        border-color: rgba(16, 185, 129, 0.35);
        color: #34d399;
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

    /* Live Intelligence Feed Demarcated Container Card */
    div[data-testid="stElementContainer"]:has(.st-key-live_intelligence_feed_container),
    div[data-testid="element-container"]:has(.st-key-live_intelligence_feed_container),
    div[data-testid="stElementContainer"].st-key-live_intelligence_feed_container,
    div[data-testid="element-container"].st-key-live_intelligence_feed_container {
        margin-top: 10px !important;
        padding-top: 0 !important;
    }
    .st-key-live_intelligence_feed_container,
    div[data-testid="stVerticalBlock"].st-key-live_intelligence_feed_container,
    div[data-testid="stVerticalBlockBorderWrapper"].st-key-live_intelligence_feed_container,
    .st-key-live_intelligence_feed_container[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-feed_sentiment_pills) {
        display: block !important;
        box-sizing: border-box !important;
        clear: both !important;
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 8px !important;
        box-shadow: var(--card-shadow) !important;
        padding: 12px 16px 14px 16px !important;
        margin-top: 10px !important;
        margin-bottom: 12px !important;
        position: relative !important;
        z-index: 1 !important;
        gap: 6px !important;
    }

    /* Prevent inner double nested border if Streamlit renders child border wrapper */
    .st-key-live_intelligence_feed_container div[data-testid="stVerticalBlockBorderWrapper"]:not(.st-key-live_intelligence_feed_container) {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .st-key-live_intelligence_feed_container div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-feed_sentiment_pills) > div[data-testid="stVerticalBlock"] {
        padding: 0 !important;
        gap: 6px !important;
    }

    /* Inner Header Row: Seamless Single Tile with Zero Nested Borders */
    .st-key-live_intelligence_feed_container div[data-testid="stHorizontalBlock"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-feed_sentiment_pills) div[data-testid="stHorizontalBlock"],
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) {
        align-items: center !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    .st-key-live_intelligence_feed_container div[data-testid="stHorizontalBlock"] div[data-testid="stElementContainer"],
    .st-key-live_intelligence_feed_container div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"],
    .st-key-live_intelligence_feed_container div[data-testid="stHorizontalBlock"] div[data-testid="column"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-feed_sentiment_pills) div[data-testid="stElementContainer"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-feed_sentiment_pills) div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) div[data-testid="stElementContainer"],
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) > div[data-testid="column"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Live Intelligence Feed Header Perfect Vertical Alignment & Distinct Sentiment Color Pills */
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) {
        align-items: center !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) div[data-testid="stElementContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) div[data-testid="stMarkdownContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-feed_sentiment_pills) div[data-testid="stMarkdownContainer"] > p {
        margin: 0 !important;
        padding: 0 !important;
    }
    .st-key-feed_sentiment_pills {
        margin: 0 !important;
        padding: 0 !important;
    }
    .st-key-feed_sentiment_pills,
    .st-key-feed_sentiment_pills > div {
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
        width: 100% !important;
        margin-left: auto !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    .st-key-feed_sentiment_pills div[data-testid="stPills"],
    .st-key-feed_sentiment_pills div[data-testid="stSegmentedControl"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"],
    .st-key-feed_sentiment_pills div[role="radiogroup"] {
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
        margin-left: auto !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding: 0 !important;
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
    /* 1. All Button (Clean Neutral) */
    .st-key-feed_sentiment_pills button:nth-of-type(1),
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1),
    .st-key-feed_sentiment_pills div[role="radiogroup"] > button:nth-of-type(1),
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button {
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        color: var(--text-primary) !important;
        background: rgba(255, 255, 255, 0.04) !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(1):hover,
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1):hover,
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button:hover {
        border-color: rgba(255, 255, 255, 0.28) !important;
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
    }
    .st-key-feed_sentiment_pills button:nth-of-type(1)[aria-checked="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(1)[data-checked="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(1)[aria-selected="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(1)[data-selected="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(1)[data-selected],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1)[aria-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1)[data-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1)[aria-selected="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1)[data-selected="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(1)[data-selected],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button[aria-checked="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button[aria-selected="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button[data-selected="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(1) button[data-selected] {
        background: rgba(255, 255, 255, 0.14) !important;
        border-color: rgba(255, 255, 255, 0.35) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
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
    .st-key-feed_sentiment_pills button:nth-of-type(2)[aria-selected="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(2)[data-selected="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(2)[data-selected],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2)[aria-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2)[data-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2)[aria-selected="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2)[data-selected="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(2)[data-selected],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(2) button[aria-checked="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(2) button[aria-selected="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(2) button[data-selected="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(2) button[data-selected] {
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
    .st-key-feed_sentiment_pills button:nth-of-type(3)[aria-selected="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(3)[data-selected="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(3)[data-selected],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3)[aria-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3)[data-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3)[aria-selected="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3)[data-selected="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(3)[data-selected],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(3) button[aria-checked="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(3) button[aria-selected="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(3) button[data-selected="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(3) button[data-selected] {
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
    .st-key-feed_sentiment_pills button:nth-of-type(4)[aria-selected="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(4)[data-selected="true"],
    .st-key-feed_sentiment_pills button:nth-of-type(4)[data-selected],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4)[aria-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4)[data-checked="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4)[aria-selected="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4)[data-selected="true"],
    .st-key-feed_sentiment_pills [data-testid="stPills"] button:nth-of-type(4)[data-selected],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(4) button[aria-checked="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(4) button[aria-selected="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(4) button[data-selected="true"],
    .st-key-feed_sentiment_pills ul[data-testid="stPills-list"] li:nth-of-type(4) button[data-selected] {
        background: rgba(148, 163, 184, 0.25) !important;
        border-color: #94a3b8 !important;
        color: #cbd5e1 !important;
        box-shadow: 0 0 10px rgba(148, 163, 184, 0.25) !important;
    }
    
    /* Dedicated Mini Index Grid & Card Styling */
    .mini-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
        gap: 6px;
        margin-top: 10px !important;
        margin-bottom: 0 !important;
        padding-top: 10px !important;
        border-top: 1px solid var(--card-border) !important;
        box-sizing: border-box !important;
        width: 100%;
    }
    .mini-index-card {
        background: var(--card-bg) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 6px;
        padding: 6px 7px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-sizing: border-box;
        box-shadow: var(--card-shadow);
        min-width: 0;
        overflow: hidden;
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
        border-color: rgba(255, 255, 255, 0.16) !important;
        transform: translateY(-1px);
    }
    .news-item-card:last-child {
        margin-bottom: 0;
    }
</style>
""".replace("__THEME_VARS__", theme_css_vars)



def get_theme_css(is_dark: bool = True) -> str:
    """Returns the rendered CSS block with active theme variables."""
    return css_theme_template

def inject_global_styles(is_dark: bool = True):
    """Injects master permanent dark theme CSS into Streamlit page."""
    st.session_state['theme_toggle'] = True
    st.markdown(css_theme_template, unsafe_allow_html=True)
