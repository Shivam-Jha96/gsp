import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Ensure we can import from the sibling directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.client import get_db_client
from signal_engine.ema import calculate_ema

st.set_page_config(page_title="Macro-Sentiment Terminal", layout="wide", initial_sidebar_state="expanded")

# --- Institutional UI Styling ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        max-width: 95%;
    }
    h1, h2, h3, h4 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 400;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

st.title("GLOBAL MACRO-SENTIMENT TERMINAL")
st.markdown("<p style='color: #888; font-size: 1.1rem; margin-top: -15px;'>QUANTITATIVE MARKET SENTIMENT AGGREGATION & ANALYSIS</p>", unsafe_allow_html=True)
st.markdown("---")

@st.cache_data(ttl=30)
def load_data():
    """Fetch the latest signals and payloads from Supabase."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.warning("DATABASE_URL NOT CONFIGURED. SHOWING SIMULATED DATA.")
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
            "raw_text": ["Mock headline summary indicating market movement..."] * 20
        })
        return mock_signals, mock_payloads

    try:
        client = get_db_client()
        with client.get_connection() as conn:
            query_signals = """
                SELECT timestamp, market_region, sentiment_score 
                FROM event_signals 
                ORDER BY timestamp DESC 
                LIMIT 500
            """
            df_signals = pd.read_sql(query_signals, conn)
            
            query_payloads = """
                SELECT s.timestamp, s.market_region, s.sentiment_score, p.raw_text, p.applied_okf_rules
                FROM event_signals s
                JOIN event_payloads p ON s.id = p.id
                ORDER BY s.timestamp DESC
                LIMIT 40
            """
            df_payloads = pd.read_sql(query_payloads, conn)
            
        return df_signals, df_payloads
    except Exception as e:
        st.error(f"DATABASE CONNECTION FAILURE: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_signals, df_payloads = load_data()

if not df_signals.empty:
    df_signals['sentiment_index'] = df_signals['sentiment_score'] * 100
    df_payloads['sentiment_index'] = df_payloads['sentiment_score'] * 100

    # --- Sidebar Parameters ---
    with st.sidebar:
        st.markdown("### TERMINAL PARAMETERS")
        
        regions = df_signals['market_region'].unique().tolist()
        selected_region = st.multiselect("MARKET REGIONS", regions, default=regions)
        
        ema_window = st.slider("EMA PERIODS (HOURS)", min_value=1, max_value=24, value=4)
        
        st.markdown("---")
        st.caption("SYSTEM STATUS: ONLINE\n\nINFERENCE ENGINE: GEMINI 3.5 FLASH")

    filtered_signals = df_signals[df_signals['market_region'].isin(selected_region)].copy()
    
    if not filtered_signals.empty:
        filtered_signals.sort_values('timestamp', inplace=True)
        
        ema_series = calculate_ema(filtered_signals, window=ema_window, column='sentiment_index')
        filtered_signals['EMA_Index'] = ema_series
        
        current_ema = ema_series.iloc[-1] if len(ema_series) > 0 else 0
        previous_ema = ema_series.iloc[-2] if len(ema_series) > 1 else 0
        delta = current_ema - previous_ema
        
        if current_ema > 10 and delta > 0:
            trend, trend_color = "STRONG BULLISH", "normal"
        elif current_ema > 0:
            trend, trend_color = "SLIGHTLY BULLISH", "normal"
        elif current_ema < -10 and delta < 0:
            trend, trend_color = "STRONG BEARISH", "inverse"
        elif current_ema < 0:
            trend, trend_color = "SLIGHTLY BEARISH", "inverse"
        else:
            trend, trend_color = "NEUTRAL", "off"

        # --- Key Performance Indicators ---
        kpi_cols = st.columns(4)
        with kpi_cols[0].container(border=True):
            st.metric(f"CURRENT {ema_window}H EMA INDEX", f"{current_ema:.1f}", f"{delta:.1f}", delta_color=trend_color)
        with kpi_cols[1].container(border=True):
            st.metric("AGGREGATE MARKET BIAS", trend)
        with kpi_cols[2].container(border=True):
            st.metric("MONITORED REGIONS", len(selected_region))
        with kpi_cols[3].container(border=True):
            st.metric("ANALYZED EVENTS", len(filtered_signals))

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Charting Area ---
        st.markdown("### AGGREGATE SENTIMENT TRAJECTORY")
        with st.container(border=True):
            fig = go.Figure()
            
            colors = px.colors.qualitative.Bold
            for i, region in enumerate(selected_region):
                region_data = filtered_signals[filtered_signals['market_region'] == region]
                fig.add_trace(go.Scatter(
                    x=region_data['timestamp'], y=region_data['sentiment_index'],
                    mode='markers', name=f'{region} Data',
                    marker=dict(color=colors[i % len(colors)], size=6, opacity=0.6)
                ))
            
            fig.add_trace(go.Scatter(
                x=filtered_signals['timestamp'], y=filtered_signals['EMA_Index'],
                mode='lines', name=f'Global {ema_window}-Period Trend',
                line=dict(color='#00CC96' if current_ema >= 0 else '#FF4B4B', width=4)
            ))
            
            fig.add_hline(y=0, line_dash="dash", line_color="rgba(150,150,150,0.5)", annotation_text="Neutral Base")
            
            fig.update_layout(
                height=450,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Timeline",
                yaxis_title="Market Optimism Index (-100 to +100)",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            # Make gridlines very faint
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(150,150,150,0.1)')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(150,150,150,0.1)')
            
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### REGIONAL NEWS INGESTION")

        # --- Region-wise Columnar Feeds ---
        if not df_payloads.empty:
            num_regions = len(selected_region)
            cols = st.columns(num_regions, gap="medium")
            
            for idx, region in enumerate(selected_region):
                with cols[idx].container(border=True):
                    st.markdown(f"<h4 style='text-align: center;'>{region} FEED</h4>", unsafe_allow_html=True)
                    st.divider()
                    
                    region_payloads = df_payloads[df_payloads['market_region'] == region]
                    
                    if not region_payloads.empty:
                        with st.container(height=450):
                            for _, row in region_payloads.iterrows():
                                score = row['sentiment_index']
                                time_str = pd.to_datetime(row['timestamp']).strftime('%b %d, %H:%M')
                                
                                color = "green" if score > 10 else "red" if score < -10 else "gray"
                                
                                st.caption(f"{time_str} | **Index: :{color}[{score:.1f}]**")
                                st.markdown(f"<div style='font-size:0.9rem; line-height:1.4;'>{row['raw_text']}</div>", unsafe_allow_html=True)
                                st.divider()
                    else:
                        st.info(f"No pending events for {region}.")
        else:
            st.info("No recent news events in database.")
    else:
        st.warning("No data found for the selected parameters.")
else:
    st.info("Database empty. Run the ingestion engine to populate.")
