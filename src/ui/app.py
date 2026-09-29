import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.client import get_db_client
from signal_engine.ema import calculate_ema

st.set_page_config(page_title="Digital Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- CSS to match the provided screenshot ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F4F6F8;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1600px;
    }
    .main-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333333;
        margin-bottom: 20px;
    }
    .filter-label {
        font-size: 0.8rem;
        color: #888888;
        margin-bottom: -10px;
    }
    
    /* White Card Style for everything */
    .white-card {
        background-color: #FFFFFF;
        border-radius: 8px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #EAEAEA;
    }
    
    /* Left Column Metrics */
    .metric-title {
        font-size: 0.85rem;
        color: #777777;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #222222;
        margin-bottom: 5px;
    }
    .metric-sub {
        font-size: 0.85rem;
        font-weight: 600;
    }
    .metric-sub.green { color: #4CAF50; }
    .metric-sub.red { color: #F44336; }
    .metric-sub.gray { color: #888888; }
    .metric-footer {
        font-size: 0.7rem;
        color: #AAAAAA;
        margin-top: 5px;
    }
    
    .chart-title {
        font-size: 0.9rem;
        color: #777777;
        margin-bottom: 15px;
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
        dates = pd.date_range(end=now, periods=100, freq='h')
        import numpy as np
        np.random.seed(42)
        scores = np.random.uniform(-1, 1, size=len(dates))
        mock_signals = pd.DataFrame({
            "timestamp": dates,
            "market_region": np.random.choice(["US", "UK", "IN", "JP"], size=len(dates)),
            "sentiment_score": scores
        })
        mock_payloads = pd.DataFrame({
            "timestamp": dates[-20:],
            "market_region": mock_signals['market_region'].iloc[-20:].values,
            "sentiment_score": mock_signals['sentiment_score'].iloc[-20:].values,
            "raw_text": ["Market opening shows mixed signals..."] * 20
        })
        return mock_signals, mock_payloads

    try:
        client = get_db_client()
        with client.get_connection() as conn:
            query_signals = "SELECT timestamp, market_region, sentiment_score FROM event_signals ORDER BY timestamp DESC LIMIT 500"
            df_signals = pd.read_sql(query_signals, conn)
            
            query_payloads = """
                SELECT s.timestamp, s.market_region, s.sentiment_score, p.raw_text
                FROM event_signals s JOIN event_payloads p ON s.id = p.id
                ORDER BY s.timestamp DESC LIMIT 40
            """
            df_payloads = pd.read_sql(query_payloads, conn)
        return df_signals, df_payloads
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_signals, df_payloads = load_data()

if not df_signals.empty:
    df_signals['sentiment_index'] = df_signals['sentiment_score'] * 100
    df_payloads['sentiment_index'] = df_payloads['sentiment_score'] * 100

    st.markdown('<div class="main-header">Macro-Sentiment Dashboard</div>', unsafe_allow_html=True)
    
    # --- Top Row: Filters (like the screenshot) ---
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 3])
    
    with filter_col1:
        st.markdown('<div class="filter-label">Date Range</div>', unsafe_allow_html=True)
        date_range = st.selectbox("", ["This Week", "Today", "This Month"], label_visibility="collapsed")
    with filter_col2:
        st.markdown('<div class="filter-label">Regions</div>', unsafe_allow_html=True)
        regions = df_signals['market_region'].unique().tolist()
        selected_region = st.multiselect("", regions, default=regions, label_visibility="collapsed")
    with filter_col3:
        st.markdown('<div class="filter-label">EMA Window</div>', unsafe_allow_html=True)
        ema_window = st.selectbox("", [4, 8, 12, 24], index=0, label_visibility="collapsed")

    filtered_signals = df_signals[df_signals['market_region'].isin(selected_region)].copy()
    
    if not filtered_signals.empty:
        filtered_signals.sort_values('timestamp', inplace=True)
        ema_series = calculate_ema(filtered_signals, window=ema_window, column='sentiment_index')
        filtered_signals['EMA_Index'] = ema_series
        
        current_ema = ema_series.iloc[-1] if len(ema_series) > 0 else 0
        previous_ema = ema_series.iloc[-2] if len(ema_series) > 1 else 0
        delta = current_ema - previous_ema
        
        # --- Main Layout Split (1 Narrow Left, 1 Wide Right) ---
        left_col, right_col = st.columns([1.2, 4])
        
        with left_col:
            # 1. Global Index
            delta_color = "green" if delta > 0 else "red" if delta < 0 else "gray"
            arrow = "↑" if delta > 0 else "↓" if delta < 0 else ""
            st.markdown(f"""
            <div class="white-card">
                <div class="metric-title">Global Optimism Index</div>
                <div class="metric-value">{current_ema:+.1f}</div>
                <div class="metric-sub {delta_color}">{arrow} {abs(delta):.1f}%</div>
                <div class="metric-footer">vs previous period</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. Market Bias
            bias = "Bullish" if current_ema > 5 else "Bearish" if current_ema < -5 else "Neutral"
            b_color = "green" if bias == "Bullish" else "red" if bias == "Bearish" else "gray"
            st.markdown(f"""
            <div class="white-card">
                <div class="metric-title">Market Bias</div>
                <div class="metric-value">{bias}</div>
                <div class="metric-sub {b_color}">{ema_window}H Window</div>
                <div class="metric-footer">based on moving average</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 3. Volume
            st.markdown(f"""
            <div class="white-card">
                <div class="metric-title">Total News Volume</div>
                <div class="metric-value">{len(filtered_signals)}</div>
                <div class="metric-sub gray">Articles</div>
                <div class="metric-footer">in selected regions</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 4. Regions Active
            st.markdown(f"""
            <div class="white-card">
                <div class="metric-title">Active Markets</div>
                <div class="metric-value">{len(selected_region)}</div>
                <div class="metric-sub gray">Regions</div>
                <div class="metric-footer">currently monitored</div>
            </div>
            """, unsafe_allow_html=True)

        with right_col:
            # --- Large Area Chart at the top of the right column ---
            st.markdown('<div class="white-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-title">Aggregate Market Optimism Over Time</div>', unsafe_allow_html=True)
            
            # Smooth Filled Area Chart (like the screenshot)
            fig_area = go.Figure()
            
            # Add smooth filled area for EMA
            fig_area.add_trace(go.Scatter(
                x=filtered_signals['timestamp'], y=filtered_signals['EMA_Index'],
                mode='lines',
                line=dict(color='#70AD47', width=2, shape='spline'),
                fill='tozeroy',
                fillcolor='rgba(112, 173, 71, 0.3)',
                name='Global EMA'
            ))
            
            fig_area.update_layout(
                height=450, margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis_title="", yaxis_title="",
                xaxis=dict(showgrid=True, gridcolor='#F0F0F0'),
                yaxis=dict(showgrid=True, gridcolor='#F0F0F0')
            )
            st.plotly_chart(fig_area, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Regional News Feeds at the Bottom ---
        st.markdown('<div class="main-header" style="margin-top: 20px; font-size: 1.2rem;">Regional News Ingestion</div>', unsafe_allow_html=True)
        if not df_payloads.empty:
            cols = st.columns(len(selected_region))
            for idx, region in enumerate(selected_region):
                with cols[idx]:
                    html_feed = f"""
                    <div class="white-card" style="padding: 15px; height: 350px; overflow-y: auto;">
                        <div class="chart-title" style="margin-bottom: 10px; font-weight: bold; color: #333;">{region} FEED</div>
                    """
                    
                    region_payloads = df_payloads[df_payloads['market_region'] == region]
                    for _, row in region_payloads.iterrows():
                        color = "#70AD47" if row['sentiment_index'] > 0 else "#ED7D31" if row['sentiment_index'] < 0 else "#888"
                        time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M')
                        
                        html_feed += f'''
<div style="border-bottom: 1px solid #EEE; padding-bottom: 10px; margin-bottom: 10px;">
    <div style="font-size: 0.75rem; color: #888; display: flex; justify-content: space-between;">
        <span>{time_str}</span>
        <span style="color: {color}; font-weight: 600;">{row['sentiment_index']:+.1f}</span>
    </div>
    <div style="font-size: 0.85rem; color: #444; line-height: 1.4;">{row['raw_text']}</div>
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
