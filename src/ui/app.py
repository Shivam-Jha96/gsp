import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys

# Ensure we can import from the sibling directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.client import get_db_client
from signal_engine.ema import calculate_ema

st.set_page_config(page_title="Macro-Sentiment Tracker", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for Polished UI ---
st.markdown("""
<style>
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* News Feed Cards */
    .news-card {
        background-color: #262730;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        border-left: 5px solid #555;
    }
    .news-card.bullish { border-left-color: #00CC96; }
    .news-card.bearish { border-left-color: #EF553B; }
    .news-card.neutral { border-left-color: #636EFA; }
    
    .news-header { display: flex; justify-content: space-between; font-size: 0.85rem; color: #aaa; margin-bottom: 8px;}
    .news-body { font-size: 0.95rem; line-height: 1.4; color: #eee; }
    .region-badge { background: #333; padding: 2px 8px; border-radius: 12px; font-weight: bold; color: #fff;}
</style>
""", unsafe_allow_html=True)

st.title("🌍 Global Macro-Sentiment Tracker")
st.markdown("Real-time AI-driven market prediction dashboard analyzing global financial news.")

@st.cache_data(ttl=30)
def load_data():
    """Fetch the latest signals and payloads from Supabase."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.warning("⚠️ DATABASE_URL environment variable is not set. Showing mock data.")
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
                LIMIT 30
            """
            df_payloads = pd.read_sql(query_payloads, conn)
            
        return df_signals, df_payloads
    except Exception as e:
        st.error(f"Failed to fetch data from database: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_signals, df_payloads = load_data()

if not df_signals.empty:
    # --- Sidebar Configuration ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.markdown("Customize your sentiment view.")
        
        regions = df_signals['market_region'].unique().tolist()
        selected_region = st.multiselect("🌍 Filter Regions", regions, default=regions)
        
        st.divider()
        st.subheader("Signal Engine")
        ema_window = st.slider("EMA Smoothing Window", min_value=1, max_value=24, value=4, help="Adjust the Exponential Moving Average window size (in periods).")
        
        st.divider()
        st.info("Pipeline Status: **Active** ✅\\n\\nAI Engine: **Gemini 3.5 Flash Lite**")

    # Filter data
    filtered_signals = df_signals[df_signals['market_region'].isin(selected_region)].copy()
    
    if not filtered_signals.empty:
        filtered_signals.sort_values('timestamp', inplace=True)
        
        # Calculate Dynamic EMA
        ema_series = calculate_ema(filtered_signals, window=ema_window)
        filtered_signals['EMA'] = ema_series
        
        current_ema = ema_series.iloc[-1] if len(ema_series) > 0 else 0
        previous_ema = ema_series.iloc[-2] if len(ema_series) > 1 else 0
        delta = current_ema - previous_ema
        
        if current_ema > 0.1 and delta > 0:
            trend, trend_color = "Strong Bullish 🟢", "normal"
        elif current_ema > 0:
            trend, trend_color = "Slightly Bullish ↗️", "normal"
        elif current_ema < -0.1 and delta < 0:
            trend, trend_color = "Strong Bearish 🔴", "inverse"
        elif current_ema < 0:
            trend, trend_color = "Slightly Bearish ↘️", "inverse"
        else:
            trend, trend_color = "Neutral ⚖️", "off"

        # --- Top KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(f"Current {ema_window}-Period EMA", f"{current_ema:.3f}", f"{delta:.3f}", delta_color=trend_color)
        col2.metric("Market Trend", trend)
        col3.metric("Monitored Regions", len(selected_region))
        col4.metric("Analyzed Events", len(filtered_signals))

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Main Dashboard Area ---
        st.subheader("📈 Macro-Sentiment Trajectory")
        
        # Polished Plotly Chart (Full Width)
        fig = go.Figure()
        
        # Scatter for raw sentiment
        fig.add_trace(go.Scatter(
            x=filtered_signals['timestamp'], y=filtered_signals['sentiment_score'],
            mode='markers', name='Raw Sentiment',
            marker=dict(color='rgba(150, 150, 150, 0.4)', size=8)
        ))
        
        # Line for EMA
        fig.add_trace(go.Scatter(
            x=filtered_signals['timestamp'], y=filtered_signals['EMA'],
            mode='lines', name=f'{ema_window}-Period EMA',
            line=dict(color='#00CC96' if current_ema >= 0 else '#EF553B', width=4)
        ))
        
        # Zero Baseline
        fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)", annotation_text="Neutral Baseline")
        
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Time",
            yaxis_title="Sentiment Score (-1.0 to +1.0)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.subheader("📰 Regional News Feeds")

        # --- Region-wise Columnar Feeds ---
        if not df_payloads.empty:
            # Create a dynamic number of columns based on how many regions are selected
            num_regions = len(selected_region)
            cols = st.columns(num_regions)
            
            for idx, region in enumerate(selected_region):
                with cols[idx]:
                    st.markdown(f"#### {region} Feed")
                    
                    region_payloads = df_payloads[df_payloads['market_region'] == region]
                    
                    if not region_payloads.empty:
                        # Create a scrolling container for each region
                        st.markdown('<div style="height: 500px; overflow-y: auto; padding-right: 10px;">', unsafe_allow_html=True)
                        
                        for _, row in region_payloads.iterrows():
                            score = row['sentiment_score']
                            if score > 0.1: theme = "bullish"
                            elif score < -0.1: theme = "bearish"
                            else: theme = "neutral"
                            
                            time_str = pd.to_datetime(row['timestamp']).strftime('%b %d, %H:%M')
                            
                            st.markdown(f"""
                            <div class="news-card {theme}">
                                <div class="news-header">
                                    <span>{time_str}</span>
                                    <span style="font-weight: bold;">Score: {score:.2f}</span>
                                </div>
                                <div class="news-body">{row['raw_text']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.info(f"No recent news available for {region}.")
        else:
            st.info("No recent news events.")
    else:
        st.warning("No data found for the selected regions.")
else:
    st.info("No data available to display. Run the ingestion pipeline to fetch data.")
