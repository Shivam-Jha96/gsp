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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1600px;
    }
    
    /* Professional Headers */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.03em;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 2px solid #E2E8F0;
    }
    
    /* Modern Card Style with unique color coding */
    .white-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        padding: 24px;
        margin-bottom: 20px;
        border: 1px solid #F1F5F9;
        border-top: 4px solid #E2E8F0; /* Default */
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .white-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
    }
    .border-blue { border-top-color: #3B82F6 !important; }
    .border-green { border-top-color: #10B981 !important; }
    .border-purple { border-top-color: #8B5CF6 !important; }
    .border-orange { border-top-color: #F59E0B !important; }
    .border-indigo { border-top-color: #6366F1 !important; }
    
    /* Override Streamlit native container border */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid #F1F5F9 !important;
    }
    
    /* Metrics */
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E293B;
        letter-spacing: -0.02em;
        margin-bottom: 4px;
    }
    .metric-sub {
        font-size: 0.9rem;
        font-weight: 600;
    }
    .green { color: #10B981 !important; }
    .red { color: #EF4444 !important; }
    .gray { color: #94A3B8 !important; }
    
    .metric-footer {
        font-size: 0.75rem;
        color: #94A3B8;
        border-top: 1px solid #F1F5F9;
        padding-top: 10px;
        margin-top: 10px;
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

    st.markdown('<div class="main-header">Macro-Sentiment Dashboard</div>', unsafe_allow_html=True)
    
    # --- Top Row: Filters Using Native Labels ---
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([1, 1, 1, 1.2, 1.2])
    
    with filter_col1:
        date_range = st.selectbox("Timeframe", ["24H", "12H", "6H", "4H", "7D", "1M", "1Y", "All"], index=0)
    with filter_col2:
        regions = df_signals['market_region'].unique().tolist()
        default_ix = regions.index("US") if "US" in regions else 0
        selected_region = st.selectbox("Region", regions, index=default_ix)
    with filter_col3:
        ema_window = st.selectbox("EMA Window (Periods)", [4, 8, 12, 24], index=0)
    with filter_col4:
        tz_options = {
            "Asia/Kolkata (IST)": "Asia/Kolkata",
            "UTC": "UTC",
            "America/New_York (EST)": "America/New_York",
            "Europe/London (GMT)": "Europe/London",
            "Asia/Tokyo (JST)": "Asia/Tokyo"
        }
        display_tz = st.selectbox("Timezone", list(tz_options.keys()), index=0)
        target_tz = tz_options[display_tz]
    with filter_col5:
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
            
        now = pd.Timestamp.utcnow()
        if date_range == "4H": cutoff = now - pd.Timedelta(hours=4)
        elif date_range == "6H": cutoff = now - pd.Timedelta(hours=6)
        elif date_range == "12H": cutoff = now - pd.Timedelta(hours=12)
        elif date_range == "24H": cutoff = now - pd.Timedelta(hours=24)
        elif date_range == "7D": cutoff = now - pd.Timedelta(days=7)
        elif date_range == "1M": cutoff = now - pd.Timedelta(days=30)
        elif date_range == "1Y": cutoff = now - pd.Timedelta(days=365)
        
        filtered_signals = filtered_signals[filtered_signals['timestamp'] >= cutoff]
    
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
            st.markdown(f"""
            <div class="white-card border-blue">
                <div class="metric-title">Aggregate Optimism Index</div>
                <div class="metric-value">{current_ema:+.1f}</div>
                <div class="metric-sub {delta_color}">{arrow} {abs(delta):.1f}%</div>
                <div class="metric-footer">vs previous period</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. Market Bias
            bias = "Bullish" if current_ema > 5 else "Bearish" if current_ema < -5 else "Neutral"
            b_color = "green" if bias == "Bullish" else "red" if bias == "Bearish" else "gray"
            st.markdown(f"""
            <div class="white-card border-purple">
                <div class="metric-title">Market Bias</div>
                <div class="metric-value">{bias}</div>
                <div class="metric-sub {b_color}">{ema_window} Period Window</div>
                <div class="metric-footer">based on moving average</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 3. Volume
            st.markdown(f"""
            <div class="white-card border-orange">
                <div class="metric-title">Total News Volume</div>
                <div class="metric-value">{len(filtered_signals)}</div>
                <div class="metric-sub gray">Articles</div>
                <div class="metric-footer">in selected region</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 4. Indices Active
            tracked_count = filtered_signals['index_ticker'].nunique()
            st.markdown(f"""
            <div class="white-card border-green">
                <div class="metric-title">Tracked Indices</div>
                <div class="metric-value">{tracked_count}</div>
                <div class="metric-sub gray">In {selected_region}</div>
                <div class="metric-footer">currently monitored</div>
            </div>
            """, unsafe_allow_html=True)

        with right_col:
            # --- Large Area Chart at the top of the right column ---
            with st.container(border=True):
                st.markdown('<div class="section-header">Aggregate Market Optimism Over Time</div>', unsafe_allow_html=True)
                
                fig_area = go.Figure()
                
                # Plot overlapping filled areas for each specific Index
                colors = px.colors.qualitative.Pastel
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
                        line=dict(width=1, color=colors[i % len(colors)]),
                        marker=dict(size=4),
                        fill='tozeroy',
                        opacity=0.5
                    ))
                
                # Add smooth thick line for Global EMA Trend on top
                fig_area.add_trace(go.Scatter(
                    x=df_trend['timestamp'], y=df_trend['EMA_Index'],
                    mode='lines+markers',
                    line=dict(color='#64748B', width=2, shape='linear'),
                    marker=dict(size=6, color='#64748B', line=dict(color='white', width=1)),
                    name=f'{selected_region} Mean (EMA)'
                ))
                
                fig_area.update_layout(
                    height=450, margin=dict(l=0, r=0, t=10, b=0),
                    plot_bgcolor="white", paper_bgcolor="white",
                    xaxis_title="", yaxis_title="Optimism Index",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#4B5563")),
                    xaxis=dict(showgrid=True, gridcolor='#F0F0F0'),
                    yaxis=dict(
                        showgrid=True, gridcolor='#F0F0F0',
                        range=[-100, 100],
                        zeroline=True, zerolinecolor='#AAAAAA', zerolinewidth=2,
                        tickmode='array', tickvals=[-100, -50, 0, 50, 100]
                    )
                )
                st.plotly_chart(fig_area, use_container_width=True)

            # --- Mini KPI Tiles for Individual Indices ---
            st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
            valid_tickers = [t for t in tickers if t != 'UNKNOWN']
            if valid_tickers:
                index_cols = st.columns(len(valid_tickers))
                for idx, ticker in enumerate(valid_tickers):
                    latest_score = pivot_df[ticker].iloc[-1] if len(pivot_df) > 0 else 0
                    prev_score = pivot_df[ticker].iloc[-2] if len(pivot_df) > 1 else 0
                    delta_idx = latest_score - prev_score
                    
                    d_color = "green" if delta_idx > 0 else "red" if delta_idx < 0 else "gray"
                    d_arrow = "↑" if delta_idx > 0 else "↓" if delta_idx < 0 else ""
                    
                    with index_cols[idx]:
                        st.markdown(f"""
                        <div class="white-card border-indigo" style="padding: 15px; min-height: 85px;">
                            <div class="metric-title" style="font-size: 0.8rem; margin-bottom: 5px;">{ticker}</div>
                            <div class="metric-value" style="font-size: 1.5rem;">{latest_score:+.1f}</div>
                            <div class="metric-sub {d_color}" style="font-size: 0.75rem; margin-top: 5px;">{d_arrow} {abs(delta_idx):.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)

            # --- Regional News Feeds at the Bottom (Inside Right Col) ---
            st.markdown(f'<div class="section-header" style="margin-top: 30px;">{selected_region} Live Intelligence Feed</div>', unsafe_allow_html=True)
            if not display_payloads.empty:
                html_feed = f"""
                <div class="white-card border-blue" style="padding: 20px; height: 350px; overflow-y: auto;">
                """
                
                region_payloads = display_payloads[display_payloads['market_region'] == selected_region]
                for _, row in region_payloads.iterrows():
                    color = "#10B981" if row['sentiment_index'] > 0 else "#EF4444" if row['sentiment_index'] < 0 else "#64748B"
                    time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M')
                    
                    html_feed += f'''
<div style="border-bottom: 1px solid #F1F5F9; padding-bottom: 12px; margin-bottom: 12px;">
    <div style="font-size: 0.8rem; color: #94A3B8; display: flex; justify-content: space-between; margin-bottom: 4px;">
        <span>{time_str} • <b>{row.get('index_ticker', 'Macro')}</b></span>
        <span style="color: {color}; font-weight: 700;">{row['sentiment_index']:+.1f}</span>
    </div>
    <div style="font-size: 0.95rem; color: #334155; line-height: 1.5; font-weight: 500;">{row['raw_text']}</div>
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
