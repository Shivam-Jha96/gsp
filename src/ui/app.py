import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import sys

# Ensure we can import from the sibling directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.client import get_db_client
from signal_engine.ema import calculate_ema

st.set_page_config(page_title="Global Macro-Sentiment Tracker", layout="wide")

st.title("🌍 Global Macro-Sentiment Tracker")
st.markdown("Real-time AI-driven stock prediction dashboard based on global financial news.")

@st.cache_data(ttl=60)
def load_data():
    """Fetch the latest signals and payloads from Supabase."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.warning("⚠️ DATABASE_URL environment variable is not set. Showing mock data.")
        # Generate mock data for UI testing
        now = pd.Timestamp.utcnow()
        dates = pd.date_range(end=now, periods=50, freq='h')
        import numpy as np
        np.random.seed(42)
        scores = np.random.uniform(-1, 1, size=len(dates))
        mock_signals = pd.DataFrame({
            "timestamp": dates,
            "market_region": np.random.choice(["US", "UK", "IN", "JP"], size=len(dates)),
            "sentiment_score": scores
        })
        mock_payloads = pd.DataFrame({
            "raw_text": ["Mock headline summary..."] * len(dates)
        })
        return mock_signals, mock_payloads

    try:
        client = get_db_client()
        with client.get_connection() as conn:
            # Fetch signals for charting
            query_signals = """
                SELECT timestamp, market_region, sentiment_score 
                FROM event_signals 
                ORDER BY timestamp DESC 
                LIMIT 500
            """
            df_signals = pd.read_sql(query_signals, conn)
            
            # Fetch latest news payloads
            query_payloads = """
                SELECT s.timestamp, s.market_region, s.sentiment_score, p.raw_text, p.applied_okf_rules
                FROM event_signals s
                JOIN event_payloads p ON s.id = p.id
                ORDER BY s.timestamp DESC
                LIMIT 20
            """
            df_payloads = pd.read_sql(query_payloads, conn)
            
        return df_signals, df_payloads
    except Exception as e:
        st.error(f"Failed to fetch data from database: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Load Data
df_signals, df_payloads = load_data()

if not df_signals.empty:
    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    regions = df_signals['market_region'].unique().tolist()
    selected_region = st.sidebar.multiselect("Select Regions", regions, default=regions)

    # Filter data
    filtered_signals = df_signals[df_signals['market_region'].isin(selected_region)].copy()
    filtered_signals.sort_values('timestamp', inplace=True)
    
    # --- Top KPIs ---
    col1, col2, col3 = st.columns(3)
    
    # Calculate EMA using our signal engine logic
    ema_series = calculate_ema(filtered_signals, window=4)
    current_ema = ema_series.iloc[-1] if len(ema_series) > 0 else 0
    previous_ema = ema_series.iloc[-2] if len(ema_series) > 1 else 0
    
    trend = "Bullish 🟢" if current_ema > previous_ema and current_ema > 0 else "Bearish 🔴" if current_ema < previous_ema and current_ema < 0 else "Neutral ⚪"
    
    col1.metric("Current 4-Hr EMA", f"{current_ema:.4f}", f"{(current_ema - previous_ema):.4f}")
    col2.metric("Market Trend", trend)
    col3.metric("Total Events (Filtered)", len(filtered_signals))

    # --- Charts ---
    st.subheader("Sentiment Trajectory over Time")
    
    # Add EMA to the dataframe for plotting
    filtered_signals['4_Hr_EMA'] = ema_series
    
    fig = px.line(filtered_signals, x='timestamp', y=['sentiment_score', '4_Hr_EMA'], 
                  labels={'value': 'Score', 'timestamp': 'Time'},
                  title="Raw Sentiment vs. 4-Hour EMA Filter")
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dot", annotation_text="Neutral", annotation_position="bottom right")
    st.plotly_chart(fig, use_container_width=True)
    
    # --- Recent News Data Table ---
    st.subheader("Recent Evaluated News (Document Layer)")
    if not df_payloads.empty:
        filtered_payloads = df_payloads[df_payloads['market_region'].isin(selected_region)]
        st.dataframe(
            filtered_payloads[['timestamp', 'market_region', 'sentiment_score', 'raw_text']],
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("No data available to display.")
