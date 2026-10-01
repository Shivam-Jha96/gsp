import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.client import get_db_client

st.set_page_config(page_title="Digital Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- CSS to match the provided screenshot without breaking layout ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=Montserrat:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'IBM Plex Sans', sans-serif;
        background-color: #020617 !important;
        color: #f8fafc;
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
        color: #f8fafc;
    }
    .section-header {
        font-size: 1.1rem;
        margin-bottom: 15px;
    }
    
    /* Enviro Style Glass Cards */
    .white-card {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .white-card:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
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
        background: rgba(255, 255, 255, 0.02) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: none !important;
    }
    
    /* Force Streamlit Columns to Stretch & Align Bottoms */
    [data-testid="column"] > div[data-testid="stVerticalBlock"] {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
    }
    
    /* Metrics */
    .metric-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        color: #94a3b8; /* text-muted */
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .metric-value {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.01em;
        margin-bottom: 2px;
    }
    .metric-sub {
        font-size: 0.8rem;
        font-weight: 600;
    }
    .green { color: #10b981 !important; } /* Emerald */
    .red { color: #ef4444 !important; } 
    .gray { color: #94a3b8 !important; }
    
    .metric-footer {
        font-size: 0.75rem;
        color: #64748b;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 8px;
        margin-top: 8px;
    }
    
    /* Responsive Design Adjustments */
    @media (max-width: 1024px) {
        .metric-value { font-size: 1.4rem; }
        .block-container { padding: 1rem !important; }
    }
    
    @media (max-width: 768px) {
        .metric-value { font-size: 1.2rem; }
        .metric-title { font-size: 0.7rem; }
        .white-card { padding: 10px; margin-bottom: 10px; }
        /* Disable vertical stretching on mobile so items stack cleanly */
        [data-testid="column"] > div[data-testid="stVerticalBlock"] {
            height: auto;
            justify-content: flex-start;
        }
    }

    /* Hide Streamlit native UI elements including the white top header bar */
    header[data-testid="stHeader"] {display: none !important;}
    #MainMenu {display: none !important;}
    footer {display: none !important;}
    [data-testid="collapsedControl"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

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
            "timestamp": dates[-20:],
            "market_region": mock_signals['market_region'].iloc[-20:].values,
            "index_ticker": mock_signals['index_ticker'].iloc[-20:].values,
            "sentiment_score": mock_signals['sentiment_score'].iloc[-20:].values,
            "raw_text": ["Market opening shows mixed signals..."] * 20
        })
        return mock_signals, mock_payloads

    try:
        client = get_db_client()
        with client.get_connection() as conn:
            query_signals = "SELECT timestamp, market_region, index_ticker, sentiment_score FROM event_signals ORDER BY timestamp DESC LIMIT 1000"
            df_signals = pd.read_sql(query_signals, conn)
            df_signals['timestamp'] = pd.to_datetime(df_signals['timestamp'])
            
            query_payloads = """
                SELECT s.timestamp, s.market_region, s.index_ticker, s.sentiment_score, p.raw_text
                FROM event_signals s JOIN event_payloads p ON s.id = p.id
                ORDER BY s.timestamp DESC LIMIT 40
            """
            df_payloads = pd.read_sql(query_payloads, conn)
            df_payloads['timestamp'] = pd.to_datetime(df_payloads['timestamp'])
        return df_signals, df_payloads
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_signals, df_payloads = load_data()

if not df_signals.empty:
    df_signals['sentiment_index'] = df_signals['sentiment_score'] * 100
    df_payloads['sentiment_index'] = df_payloads['sentiment_score'] * 100
    # --- Page Header with Inline Timezone ---
    header_left, tz_label_col, tz_select_col = st.columns([3.5, 0.4, 1.2])
    with header_left:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; padding-top: 8px;">
            <div style="background-color: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px; font-weight: 800; font-size: 1.1rem; letter-spacing: 1px; font-family: 'Montserrat', sans-serif;">GSP</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.01em; font-family: 'Montserrat', sans-serif;">Macro-Sentiment Terminal</div>
        </div>
        """, unsafe_allow_html=True)
    with tz_label_col:
        st.markdown("""
        <div style="padding-top: 14px; text-align: right; color: #22d3ee; font-family: 'Montserrat', sans-serif; font-weight: 700; font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase; white-space: nowrap;">TIMEZONE</div>
        """, unsafe_allow_html=True)
    with tz_select_col:
        tz_options = {
            "Asia/Kolkata (IST)": "Asia/Kolkata",
            "UTC": "UTC",
            "America/New_York (EST)": "America/New_York",
            "Europe/London (GMT)": "Europe/London",
            "Asia/Tokyo (JST)": "Asia/Tokyo"
        }
        display_tz = st.selectbox("tz", list(tz_options.keys()), index=0, label_visibility="collapsed")
        target_tz = tz_options[display_tz]
    
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-left: 3px solid #3b82f6; border-radius: 6px; padding: 14px 18px; margin: 16px 0 24px 0; color: #94a3b8; font-family: 'IBM Plex Sans', sans-serif; font-size: 0.9rem; line-height: 1.6; font-weight: 400;">
        <strong style="color: #f8fafc; font-weight: 600; font-family: 'Montserrat', sans-serif; letter-spacing: 0.02em;">THE EDGE:</strong> We solve information overload for modern investors. Our AI reads thousands of breaking global news events in real-time, instantly analyzes their market impact, and converts the chaos into a single, easy-to-read momentum score—cutting through the noise to show you exactly where the market is heading.
    </div>
    """, unsafe_allow_html=True)
    
    # --- Top Row: Filters Using Native Labels ---
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1.2])
    
    with filter_col1:
        date_range = st.selectbox("Timeframe", ["24H", "12H", "6H", "4H", "7D", "1M", "1Y", "All"], index=0)
    with filter_col2:
        regions = df_signals['market_region'].unique().tolist()
        default_ix = regions.index("US") if "US" in regions else 0
        selected_region = st.selectbox("Region", regions, index=default_ix)
    with filter_col3:
        ema_window = st.selectbox("Exponential Moving Average (Periods)", [4, 8, 12, 24], index=0)
    with filter_col4:
        # Dynamically fetch available indices for the chosen region
        active_indices = df_signals[df_signals['market_region'] == selected_region]['index_ticker'].unique().tolist()
        active_indices = [x for x in active_indices if x != 'UNKNOWN']
        chart_display = st.selectbox("Chart Display", ["All Indices"] + active_indices, index=0)

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
        if date_range == "4H": cutoff = now - pd.Timedelta(hours=4)
        elif date_range == "6H": cutoff = now - pd.Timedelta(hours=6)
        elif date_range == "12H": cutoff = now - pd.Timedelta(hours=12)
        elif date_range == "24H": cutoff = now - pd.Timedelta(hours=24)
        elif date_range == "7D": cutoff = now - pd.Timedelta(days=7)
        elif date_range == "1M": cutoff = now - pd.Timedelta(days=30)
        elif date_range == "1Y": cutoff = now - pd.Timedelta(days=365)
        
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
        if date_range in ["1M", "1Y", "All"]:
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
        
        # --- Main Layout Split (1 Narrow Left, 1 Wide Right) ---
        left_col, right_col = st.columns([1.2, 4])
        
        with left_col:
            # 1. Global Index
            delta_color = "green" if delta > 0 else "red" if delta < 0 else "gray"
            arrow = "↑" if delta > 0 else "↓" if delta < 0 else ""
            val_color = "green" if current_ema > 0 else "red" if current_ema < 0 else ""
            st.markdown(f"""
            <div class="white-card bg-blue">
                <div class="metric-title">Aggregate Optimism Index</div>
<div class="metric-value {val_color}">{current_ema:+.1f}</div>
<div class="metric-sub {delta_color}">{arrow} {abs(delta):.1f}%</div>
                <div class="metric-footer">vs previous period</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. Market Bias
            bias = "Bullish" if current_ema > 5 else "Bearish" if current_ema < -5 else "Neutral"
            b_color = "green" if bias == "Bullish" else "red" if bias == "Bearish" else "gray"
            b_val_color = "green" if bias == "Bullish" else "red" if bias == "Bearish" else ""
            st.markdown(f"""
            <div class="white-card bg-purple">
                <div class="metric-title">Market Bias</div>
<div class="metric-value {b_val_color}">{bias}</div>
<div class="metric-sub {b_color}">{ema_window} Period Window</div>
                <div class="metric-footer">based on moving average</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 3. Volume
            st.markdown(f"""
            <div class="white-card bg-orange">
                <div class="metric-title">Total News Volume</div>
<div class="metric-value">{len(filtered_signals)}</div>
<div class="metric-sub gray">Articles</div>
                <div class="metric-footer">in selected region</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 4. Indices Active
            tracked_count = filtered_signals['index_ticker'].nunique()
            st.markdown(f"""
            <div class="white-card bg-green">
                <div class="metric-title">Tracked Indices</div>
<div class="metric-value">{tracked_count}</div>
<div class="metric-sub gray">In {selected_region}</div>
                <div class="metric-footer">currently monitored</div>
            </div>
            """, unsafe_allow_html=True)

        with right_col:
            # --- Large Area Chart at the top of the right column ---
            with st.container(border=True):
                st.markdown("""
                <div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #f8fafc; font-family: 'Montserrat', sans-serif; display: flex; align-items: center; gap: 8px;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                        Aggregate Market Optimism
                    </div>
                    <div style="font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1); text-transform: uppercase;">
                        AI Sentiment Engine
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                fig_area = go.Figure()
                
                # Plot overlapping filled areas for each specific Index
                colors = ["#2962FF", "#E91E63", "#FF9800", "#9C27B0", "#00BCD4"] # Sharp terminal colors
                tickers = [c for c in pivot_df.columns if c != 'timestamp']
                
                for i, ticker in enumerate(tickers):
                    # Ignore the old placeholder data if any still exists
                    if ticker == 'UNKNOWN': 
                        continue
                        
                    # Filter based on user's Chart Display selection
                    if chart_display != "All Indices" and ticker != chart_display:
                        continue
                        
                    fig_area.add_trace(go.Scatter(
                        x=pivot_df['timestamp'], y=pivot_df[ticker],
                        mode='lines+markers', name=f'{ticker} Sentiment',
                        line=dict(width=1.5, color=colors[i % len(colors)]),
                        marker=dict(size=4),
                        fill='tozeroy',
                        opacity=0.3
                    ))
                
                # Add smooth thick line for Global EMA Trend on top
                fig_area.add_trace(go.Scatter(
                    x=df_trend['timestamp'], y=df_trend['EMA_Index'],
                    mode='lines+markers',
                    line=dict(color='#f8fafc', width=2.5, shape='linear'), 
                    marker=dict(size=6, color='#f8fafc', line=dict(color='#020617', width=1)),
                    name=f'{selected_region} Mean (EMA)'
                ))
                
                fig_area.update_layout(
                    height=490, margin=dict(l=0, r=0, t=5, b=0),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color="#f8fafc", size=11, family="IBM Plex Sans")),
                    xaxis=dict(
                        showgrid=True, gridcolor='rgba(255,255,255,0.05)',
                        title=dict(text="Timeline (UTC)", font=dict(size=11, color="#94a3b8", family="IBM Plex Sans")),
                        tickfont=dict(size=11, color="#94a3b8", family="IBM Plex Sans")
                    ),
                    yaxis=dict(
                        showgrid=True, gridcolor='rgba(255,255,255,0.05)',
                        zeroline=True, zerolinecolor='rgba(255,255,255,0.2)', zerolinewidth=2,
                        title=dict(text="Optimism Score", font=dict(size=11, color="#94a3b8", family="IBM Plex Sans")),
                        tickfont=dict(size=11, color="#f8fafc", family="IBM Plex Sans", weight="bold"),
                        side="right"
                    )
                )
                st.plotly_chart(fig_area, use_container_width=True)

            # --- Mini KPI Tiles for Individual Indices (Responsive Flexbox) ---
            valid_tickers = [t for t in tickers if t != 'UNKNOWN']
            if valid_tickers:
                # Use a CSS flexbox container instead of rigid Streamlit columns so they wrap naturally
                kpi_html = '<div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 12px;">'
                
                for ticker in valid_tickers:
                    latest_score = pivot_df[ticker].iloc[-1] if len(pivot_df) > 0 else 0
                    prev_score = pivot_df[ticker].iloc[-2] if len(pivot_df) > 1 else 0
                    delta_idx = latest_score - prev_score
                    
                    d_color = "green" if delta_idx > 0 else "red" if delta_idx < 0 else "gray"
                    d_arrow = "↑" if delta_idx > 0 else "↓" if delta_idx < 0 else ""
                    val_color = "green" if latest_score > 0 else "red" if latest_score < 0 else ""
                    
                    kpi_html += f"""<div class="white-card bg-indigo" style="flex: 1 1 130px; padding: 12px; min-height: 85px; margin-bottom: 0;">
<div class="metric-title" style="font-size: 0.75rem; margin-bottom: 4px;">{ticker}</div>
<div class="metric-value {val_color}" style="font-size: clamp(1.2rem, 2vw, 1.6rem);">{latest_score:+.1f}</div>
<div class="metric-sub {d_color}" style="font-size: 0.8rem; margin-top: 5px;">{d_arrow} {abs(delta_idx):.1f}%</div>
</div>"""
                
                kpi_html += '</div>'
                st.markdown(kpi_html, unsafe_allow_html=True)

        # --- Regional News Feeds at the Bottom (Full Width) ---
        st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-top: 30px; margin-bottom: 12px;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #f8fafc; font-family: 'Montserrat', sans-serif; display: flex; align-items: center; gap: 8px;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"></circle><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"></path></svg>
                {selected_region} Live Intelligence Feed
            </div>
            <div style="font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(245, 158, 11, 0.2); text-transform: uppercase;">
                {len(display_payloads[display_payloads['market_region'] == selected_region])} Events Detected
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not display_payloads.empty:
            html_feed = f"""
            <div class="white-card bg-orange" style="padding: 20px; height: 350px; overflow-y: auto;">
            """
            
            region_payloads = display_payloads[display_payloads['market_region'] == selected_region]
            for _, row in region_payloads.iterrows():
                sentiment = row['sentiment_index']
                color = "#10b981" if sentiment > 0 else "#ef4444" if sentiment < 0 else "#94a3b8"
                time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M')
                ticker_label = row.get('index_ticker', 'Macro')
                
                noise_tag = ""
                if sentiment == 0:
                    noise_tag = '<span style="background: rgba(148, 163, 184, 0.15); border: 1px solid rgba(148, 163, 184, 0.3); color: #94a3b8; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; margin-left: 8px;">NOISE</span>'
                
                html_feed += f'''
<div style="border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px; margin-bottom: 12px;">
    <div style="font-size: 0.8rem; color: #94a3b8; display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span>{time_str}</span>
            <span style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #f8fafc; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;">{ticker_label}</span>{noise_tag}
        </div>
        <span style="color: {color}; font-weight: 700; font-size: 0.9rem;">{sentiment:+.1f}</span>
    </div>
    <div style="font-size: 0.95rem; color: #f8fafc; line-height: 1.5; font-weight: 500;">{row['raw_text']}</div>
</div>
'''
            html_feed += "</div>"
            st.markdown(html_feed, unsafe_allow_html=True)
        else:
            st.info("No recent news events in database.")
            

    else:
        st.warning("No data found for the selected parameters.")
else:
    st.info("Database empty. Run the ingestion engine to populate.")
