import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.client import get_db_client
from signal_engine.ema import calculate_ema

st.set_page_config(page_title="Global Sentiment", layout="wide", initial_sidebar_state="expanded")

# --- Modern Custom CSS (Tailwind Inspired) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
    }
    
    .custom-metric-card {
        background: #ffffff;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        text-align: left;
    }
    .metric-label {
        color: #6B7280;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #111827;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1;
    }
    .metric-delta.positive { color: #10B981; font-size: 0.875rem; font-weight: 600; margin-top: 8px; }
    .metric-delta.negative { color: #EF4444; font-size: 0.875rem; font-weight: 600; margin-top: 8px; }
    .metric-delta.neutral { color: #6B7280; font-size: 0.875rem; font-weight: 600; margin-top: 8px; }
    
    .sidebar-header {
        color: #4B5563;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 24px;
        margin-bottom: 12px;
    }
    
    .news-container {
        background: #ffffff;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 0;
        height: 500px;
        overflow-y: auto;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }
    .news-header-title {
        background: #F9FAFB;
        padding: 12px 20px;
        border-bottom: 1px solid #E5E7EB;
        font-weight: 700;
        color: #1F2937;
        position: sticky;
        top: 0;
        z-index: 10;
        border-radius: 12px 12px 0 0;
    }
    .news-item {
        padding: 16px 20px;
        border-bottom: 1px solid #F3F4F6;
    }
    .news-item:last-child { border-bottom: none; }
    .news-meta { font-size: 0.75rem; color: #6B7280; font-weight: 500; margin-bottom: 4px; display: flex; justify-content: space-between;}
    .news-text { font-size: 0.875rem; color: #374151; line-height: 1.5; }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def load_data():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.warning("DATABASE_URL not set. Showing simulated data.")
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
            "raw_text": ["Market opening shows mixed signals amid new inflation data..."] * 20
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
                SELECT s.timestamp, s.market_region, s.sentiment_score, p.raw_text
                FROM event_signals s
                JOIN event_payloads p ON s.id = p.id
                ORDER BY s.timestamp DESC
                LIMIT 50
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

    # --- Heavily Styled Sidebar ---
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding: 10px 0 20px 0;'>
                <h1 style='color: #2563EB; margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -1px;'>GSP</h1>
                <p style='color: #9CA3AF; font-size: 11px; margin: 0; font-weight: 600; letter-spacing: 2px;'>GLOBAL SENTIMENT</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='sidebar-header'>Dashboard Controls</div>", unsafe_allow_html=True)
        regions = df_signals['market_region'].unique().tolist()
        selected_region = st.multiselect("Market Regions", regions, default=regions, label_visibility="collapsed")
        
        st.markdown("<div class='sidebar-header'>Signal Processing</div>", unsafe_allow_html=True)
        ema_window = st.slider("EMA Smoothing (Hours)", min_value=1, max_value=24, value=4, label_visibility="collapsed")
        
        st.markdown("<br><hr style='margin:0;'><br>", unsafe_allow_html=True)
        
        # Status Card in Sidebar
        st.markdown("""
            <div style='background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 12px;'>
                <div style='color: #166534; font-size: 12px; font-weight: 700; margin-bottom: 4px;'>● SYSTEM ACTIVE</div>
                <div style='color: #15803D; font-size: 11px;'>Engine: Gemini 3.5 Flash</div>
            </div>
        """, unsafe_allow_html=True)

    filtered_signals = df_signals[df_signals['market_region'].isin(selected_region)].copy()
    
    if not filtered_signals.empty:
        filtered_signals.sort_values('timestamp', inplace=True)
        
        ema_series = calculate_ema(filtered_signals, window=ema_window, column='sentiment_index')
        filtered_signals['EMA_Index'] = ema_series
        
        current_ema = ema_series.iloc[-1] if len(ema_series) > 0 else 0
        previous_ema = ema_series.iloc[-2] if len(ema_series) > 1 else 0
        delta = current_ema - previous_ema
        
        if current_ema > 10 and delta > 0:
            trend_text, delta_class, delta_text = "Strong Bullish", "positive", f"▲ +{delta:.1f} Momentum"
        elif current_ema > 0:
            trend_text, delta_class, delta_text = "Mildly Bullish", "positive", f"▲ +{delta:.1f} Momentum"
        elif current_ema < -10 and delta < 0:
            trend_text, delta_class, delta_text = "Strong Bearish", "negative", f"▼ {delta:.1f} Momentum"
        elif current_ema < 0:
            trend_text, delta_class, delta_text = "Mildly Bearish", "negative", f"▼ {delta:.1f} Momentum"
        else:
            trend_text, delta_class, delta_text = "Neutral", "neutral", f"▶ {delta:.1f} Momentum"

        # --- Top Header ---
        st.markdown("""
            <h2 style='color: #111827; font-size: 1.5rem; font-weight: 700; margin-bottom: 20px;'>Macroeconomic Sentiment Overview</h2>
        """, unsafe_allow_html=True)

        # --- Custom HTML KPI Tiles ---
        kpi_html = f"""
        <div style="display: flex; gap: 20px; margin-bottom: 30px;">
            <div class="custom-metric-card" style="flex: 1;">
                <div class="metric-label">Global Optimism Index</div>
                <div class="metric-value">{current_ema:.1f}</div>
                <div class="metric-delta {delta_class}">{delta_text}</div>
            </div>
            <div class="custom-metric-card" style="flex: 1;">
                <div class="metric-label">Market Bias</div>
                <div class="metric-value" style="font-size: 1.5rem; line-height: 1.33;">{trend_text}</div>
                <div class="metric-delta neutral">Based on {ema_window}H EMA</div>
            </div>
            <div class="custom-metric-card" style="flex: 1;">
                <div class="metric-label">Analyzed Events</div>
                <div class="metric-value">{len(filtered_signals)}</div>
                <div class="metric-delta neutral">Across {len(selected_region)} Regions</div>
            </div>
        </div>
        """
        st.markdown(kpi_html, unsafe_allow_html=True)

        # --- Charting Area ---
        fig = go.Figure()
        
        colors = px.colors.qualitative.Prism
        for i, region in enumerate(selected_region):
            region_data = filtered_signals[filtered_signals['market_region'] == region]
            fig.add_trace(go.Scatter(
                x=region_data['timestamp'], y=region_data['sentiment_index'],
                mode='markers', name=f'{region}',
                marker=dict(color=colors[i % len(colors)], size=6, opacity=0.7)
            ))
        
        fig.add_trace(go.Scatter(
            x=filtered_signals['timestamp'], y=filtered_signals['EMA_Index'],
            mode='lines', name=f'Global EMA',
            line=dict(color='#2563EB', width=4)
        ))
        
        fig.add_hline(y=0, line_dash="solid", line_color="#E5E7EB", line_width=2)
        
        fig.update_layout(
            height=400,
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            xaxis_title="",
            yaxis_title="Optimism Index",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#4B5563")),
            margin=dict(l=0, r=0, t=10, b=0),
            font=dict(family="Inter", color="#374151")
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F3F4F6', zeroline=False)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F3F4F6', zeroline=False)
        
        st.markdown("""
            <div style="background: #ffffff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1); margin-bottom: 30px;">
                <div style="font-weight: 700; color: #111827; margin-bottom: 15px;">Global Trajectory & Order Flow</div>
        """, unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # --- Region-wise Columnar Feeds ---
        st.markdown("<h3 style='color: #111827; font-size: 1.25rem; font-weight: 700; margin-bottom: 15px;'>Real-Time Regional Ingestion</h3>", unsafe_allow_html=True)
        
        if not df_payloads.empty:
            num_regions = len(selected_region)
            cols = st.columns(num_regions, gap="large")
            
            for idx, region in enumerate(selected_region):
                with cols[idx]:
                    region_payloads = df_payloads[df_payloads['market_region'] == region]
                    
                    if not region_payloads.empty:
                        html_feed = f"""
                        <div class="news-container">
                            <div class="news-header-title">{region} MARKET</div>
                        """
                        
                        for _, row in region_payloads.iterrows():
                            score = row['sentiment_index']
                            time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M')
                            
                            color = "#10B981" if score > 10 else "#EF4444" if score < -10 else "#6B7280"
                            
                            html_feed += f"""
                            <div class="news-item">
                                <div class="news-meta">
                                    <span>{time_str}</span>
                                    <span style="color: {color}; font-weight: 700;">{score:+.1f}</span>
                                </div>
                                <div class="news-text">{row['raw_text']}</div>
                            </div>
                            """
                            
                        html_feed += "</div>"
                        st.markdown(html_feed, unsafe_allow_html=True)
                    else:
                        st.info(f"No pending events for {region}.")
        else:
            st.info("No recent news events in database.")
    else:
        st.warning("No data found for the selected parameters.")
else:
    st.info("Database empty. Run the ingestion engine to populate.")
