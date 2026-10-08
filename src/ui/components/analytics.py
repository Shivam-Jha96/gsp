"""
Analytics surface component: multi-index optimism chart, EMA crossover vectors, and regional KPI cards.
"""

from typing import Optional
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from ui.components.common import make_fragment_decorator


@make_fragment_decorator(run_every="5m")
def render_analytics_surface(df_signals: Optional[pd.DataFrame] = None, get_processed_data_fn=None):
    if df_signals is None and get_processed_data_fn is not None:
        df_signals, _, _ = get_processed_data_fn()

    if df_signals is None or df_signals.empty:
        st.warning("No data found for the selected parameters.")
        return

    region_name_map = {
        "IN": "India (IN)",
        "US": "United States (US)",
        "UK": "United Kingdom (UK)",
        "JP": "Japan (JP)"
    }
    selected_region_display = st.session_state.get("filter_region", "India (IN)")
    selected_region = next((code for code, name in region_name_map.items() if name == selected_region_display), selected_region_display)
    if "(" in selected_region_display and ")" in selected_region_display and selected_region not in ["IN", "US", "UK", "JP"]:
        selected_region = selected_region_display.split("(")[-1].replace(")", "").strip()

    date_range = st.session_state.get("filter_timeframe", "7 Days")
    chart_display = st.session_state.get("filter_chart_display", "All Indices")

    tz_options = {
        "Asia/Kolkata (IST)": "Asia/Kolkata",
        "UTC": "UTC",
        "America/New_York (EST)": "America/New_York",
        "Europe/London (GMT)": "Europe/London",
        "Asia/Tokyo (JST)": "Asia/Tokyo"
    }
    tz_keys = list(tz_options.keys())
    default_tz_ix = next((i for i, k in enumerate(tz_keys) if "IST" in k), 0)
    current_selected_tz = st.session_state.get("filter_timezone", tz_keys[default_tz_ix])
    target_tz = tz_options.get(current_selected_tz, "Asia/Kolkata")
    tz_abbr = current_selected_tz.split('(')[-1].replace(')', '').strip() if '(' in current_selected_tz else current_selected_tz

    selected_ema_label = st.session_state.get("filter_ema_window", "4 Periods")
    try:
        ema_window = int(str(selected_ema_label).split()[0])
    except Exception:
        ema_window = 4

    filtered_signals = df_signals[df_signals['market_region'] == selected_region].copy()

    # --- Timeframe Filtering ---
    if not filtered_signals.empty and date_range != "All":
        if filtered_signals['timestamp'].dt.tz is None:
            filtered_signals['timestamp'] = filtered_signals['timestamp'].dt.tz_localize('UTC')

        now = pd.Timestamp.now('UTC')
        cutoff = now
        if date_range in ["4 Hours", "4 Hour", "4H"]: cutoff = now - pd.Timedelta(hours=4)
        elif date_range in ["6 Hours", "6 Hour", "6H"]: cutoff = now - pd.Timedelta(hours=6)
        elif date_range in ["12 Hours", "12 Hour", "12H"]: cutoff = now - pd.Timedelta(hours=12)
        elif date_range in ["1 Day", "1Day", "24 Hours", "24 Hour", "24H"]: cutoff = now - pd.Timedelta(hours=24)
        elif date_range in ["7 Days", "7 Day", "7D"]: cutoff = now - pd.Timedelta(days=7)
        elif date_range in ["1 Month", "1M"]: cutoff = now - pd.Timedelta(days=30)
        elif date_range in ["1 Year", "1Y"]: cutoff = now - pd.Timedelta(days=365)

        filtered_signals = filtered_signals[filtered_signals['timestamp'] >= cutoff]

    if not filtered_signals.empty:
        if filtered_signals['timestamp'].dt.tz is None:
            filtered_signals['timestamp'] = filtered_signals['timestamp'].dt.tz_localize('UTC')
        filtered_signals['timestamp'] = filtered_signals['timestamp'].dt.tz_convert(target_tz)
        filtered_signals.sort_values('timestamp', inplace=True)

        freq_str = 'h'
        if date_range in ["1 Month", "1M", "1 Year", "1Y", "All"]:
            freq_str = 'D'

        df_trend = filtered_signals.groupby(pd.Grouper(key='timestamp', freq=freq_str))['sentiment_index'].mean().dropna().reset_index()
        df_trend['EMA_Index'] = df_trend['sentiment_index'].ewm(span=ema_window, adjust=False).mean()

        current_ema = df_trend['EMA_Index'].iloc[-1] if len(df_trend) > 0 else 0
        previous_ema = df_trend['EMA_Index'].iloc[-2] if len(df_trend) > 1 else 0
        delta = current_ema - previous_ema

        plot_trend_x = df_trend['timestamp'].dt.tz_localize(None) if df_trend['timestamp'].dt.tz is not None else df_trend['timestamp']

        left_col, right_col = st.columns([1.25, 3.75])

        with left_col:
            if abs(delta) < 0.05:
                delta_str = "— No change"
                delta_pill_color = "#94a3b8"
                delta_pill_bg = "rgba(148, 163, 184, 0.15)"
                delta_pill_border = "rgba(148, 163, 184, 0.3)"
            elif delta > 0:
                delta_str = f"▲ +{abs(delta):.1f}% change"
                delta_pill_color = "#34d399"
                delta_pill_bg = "rgba(16, 185, 129, 0.15)"
                delta_pill_border = "rgba(16, 185, 129, 0.3)"
            else:
                delta_str = f"▼ -{abs(delta):.1f}% change"
                delta_pill_color = "#f87171"
                delta_pill_bg = "rgba(239, 68, 68, 0.15)"
                delta_pill_border = "rgba(239, 68, 68, 0.3)"

            val_color = "green" if current_ema > 0 else "red" if current_ema < 0 else ""

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

            total_news_count = len(filtered_signals)
            tracked_count = filtered_signals['index_ticker'].nunique()
            nv_color = "#cbd5e1"
            nv_bg = "rgba(255, 255, 255, 0.06)"
            nv_border = "rgba(255, 255, 255, 0.12)"
            ti_color = "#34d399"

            kpi_column_html = (
                '<div class="kpi-column-container">'
                '<div class="white-card kpi-card">'
                '<div class="kpi-card-content">'
                '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 2px;">'
                '<span class="metric-title" style="margin-bottom: 0;">Aggregate Optimism</span>'
                f'<span style="font-size: 0.72rem; font-weight: 700; color: var(--header-border-left); text-transform: uppercase; font-family: \'Montserrat\', sans-serif;">{selected_region}</span>'
                '</div>'
                f'<div class="metric-value metric-hero {val_color}">{current_ema:+.1f}</div>'
                '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 2px;">'
                f'<span style="font-size: 0.74rem; font-weight: 700; color: {delta_pill_color}; background: {delta_pill_bg}; border: 1px solid {delta_pill_border}; padding: 2px 7px; border-radius: 4px; font-family: \'Montserrat\', sans-serif;">{delta_str}</span>'
                '<span style="font-size: 0.78rem; color: var(--text-secondary);">vs previous period</span>'
                '</div>'
                '</div>'
                '<div class="metric-footer" style="margin-top: 6px; padding-top: 6px; font-size: 0.78rem; color: var(--text-secondary); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">'
                '<span>Confidence vector</span>'
                '<span style="color: var(--text-primary); font-weight: 600;">System-One CLM</span>'
                '</div>'
                '</div>'

                '<div class="white-card kpi-card">'
                '<div class="kpi-card-content">'
                '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 2px;">'
                '<span class="metric-title" style="margin-bottom: 0;">Market Bias</span>'
                f'<span style="font-size: 0.68rem; font-weight: 800; color: {b_color_hex}; background: {b_pill_bg}; border: 1px solid {b_pill_border}; padding: 2px 7px; border-radius: 4px; text-transform: uppercase; font-family: \'Montserrat\', sans-serif; letter-spacing: 0.04em;">{bias}</span>'
                '</div>'
                f'<div class="metric-value {b_val_color}" style="font-size: 1.55rem;">{bias}</div>'
                '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 2px;">'
                f'<span style="font-size: 0.78rem; color: var(--text-secondary);">{ema_window}-period moving average</span>'
                '</div>'
                '</div>'
                '<div class="metric-footer" style="margin-top: 6px; padding-top: 6px; font-size: 0.78rem; color: var(--text-secondary); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">'
                '<span>Signal strategy</span>'
                '<span style="color: var(--text-primary); font-weight: 600;">EMA Crossover</span>'
                '</div>'
                '</div>'

                '<div class="white-card kpi-card">'
                '<div class="kpi-card-content">'
                '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 2px;">'
                '<span class="metric-title" style="margin-bottom: 0;">Total News Volume</span>'
                f'<span style="font-size: 0.68rem; font-weight: 700; color: {nv_color}; background: {nv_bg}; border: 1px solid {nv_border}; padding: 2px 7px; border-radius: 4px; font-family: \'Montserrat\', sans-serif;">{date_range} Window</span>'
                '</div>'
                f'<div class="metric-value" style="color: var(--text-primary); font-size: 1.55rem;">{total_news_count}</div>'
                '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 2px;">'
                '<span style="font-size: 0.78rem; color: var(--text-secondary);">articles ingested</span>'
                '</div>'
                '</div>'
                '<div class="metric-footer" style="margin-top: 6px; padding-top: 6px; font-size: 0.78rem; color: var(--text-secondary); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 4px;">'
                '<span>Ingestion cadence</span>'
                '<span style="color: var(--text-primary); font-weight: 600;">Every 2 hours</span>'
                '</div>'
                '</div>'

                '<div class="white-card kpi-card">'
                '<div class="kpi-card-content">'
                '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px; margin-bottom: 2px;">'
                '<span class="metric-title" style="margin-bottom: 0;">Tracked Indices</span>'
                f'<span style="font-size: 0.68rem; font-weight: 700; color: {ti_color}; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 2px 7px; border-radius: 4px; text-transform: uppercase; font-family: \'Montserrat\', sans-serif;">{selected_region}</span>'
                '</div>'
                f'<div class="metric-value" style="color: var(--text-primary); font-size: 1.55rem;">{tracked_count}</div>'
                '<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 2px;">'
                f'<span style="font-size: 0.74rem; font-weight: 700; color: {ti_color}; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 2px 6px; border-radius: 4px; font-family: \'Montserrat\', sans-serif;">100% Active</span>'
                '<span style="font-size: 0.78rem; color: var(--text-secondary);">real-time monitored</span>'
                '</div>'
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
            with st.container(border=True, key="market_optimism_chart_container"):
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; padding: 2px 2px 8px 2px; border-bottom: 1px solid var(--card-border); margin-bottom: 6px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.30); padding: 5px; border-radius: 6px; display: flex; align-items: center;">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                        </div>
                        <div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary); font-family: 'Montserrat', sans-serif; line-height: 1.2;">Aggregate Market Optimism</div>
                            <div style="font-size: 0.78rem; color: var(--text-muted); font-family: 'IBM Plex Sans', sans-serif;">Multi-index sentiment surface & {selected_region} moving average</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 0.75rem; color: var(--text-muted); font-family: 'IBM Plex Sans', sans-serif;">Scale: [-100, +100] • {tz_abbr}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                fig_area = go.Figure()
                distinct_colors = ["#10b981", "#f59e0b", "#6366f1", "#06b6d4", "#ec4899", "#84cc16"]
                fill_colors = [
                    "rgba(16, 185, 129, 0.12)",
                    "rgba(245, 158, 11, 0.10)",
                    "rgba(99, 102, 241, 0.10)",
                    "rgba(6, 182, 212, 0.10)",
                    "rgba(236, 72, 153, 0.10)",
                    "rgba(132, 204, 22, 0.10)"
                ]
                active_tickers = [c for c in filtered_signals['index_ticker'].unique() if c != 'UNKNOWN']

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

                ema_color = '#f8fafc'
                fig_area.add_trace(go.Scatter(
                    x=plot_trend_x, y=df_trend['EMA_Index'],
                    mode='lines',
                    line=dict(color=ema_color, width=3.2, shape='linear'),
                    name=f'{selected_region} Trend ({ema_window}P EMA)'
                ))

                fig_area.update_layout(
                    height=460, margin=dict(l=8, r=44, t=28, b=24),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                        font=dict(color="#f8fafc", size=11, family="Montserrat")
                    ),
                    xaxis=dict(
                        showgrid=True, gridcolor='rgba(255,255,255,0.06)',
                        showline=True, linecolor='rgba(255,255,255,0.15)', linewidth=1,
                        ticks='outside', tickcolor='rgba(255,255,255,0.25)', ticklen=4,
                        title=dict(text=f"<b>TIMELINE • {tz_abbr}</b>", font=dict(size=11, color="#cbd5e1", family="Montserrat")),
                        tickfont=dict(size=10, color="#94a3b8", family="IBM Plex Sans")
                    ),
                    yaxis=dict(
                        range=[-105, 105],
                        dtick=25,
                        fixedrange=True,
                        showgrid=True, gridcolor='rgba(255,255,255,0.06)',
                        zeroline=True, zerolinecolor='rgba(148, 163, 184, 0.35)', zerolinewidth=1.5,
                        showline=True, linecolor='rgba(255,255,255,0.15)', linewidth=1,
                        ticks='outside', tickcolor='rgba(255,255,255,0.25)', ticklen=4,
                        title=dict(text="<b>OPTIMISM SCORE</b>", font=dict(size=11, color="#cbd5e1", family="Montserrat")),
                        tickfont=dict(size=10, color="#f8fafc", family="IBM Plex Sans"),
                        side="right"
                    )
                )
                st.plotly_chart(
                    fig_area,
                    use_container_width=True,
                    config={
                        'displayModeBar': 'hover',
                        'scrollZoom': False,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': ['zoom2d', 'zoomIn2d', 'zoomOut2d']
                    }
                )

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
                            t_status_color = "#94a3b8"
                            t_status_bg = "rgba(148, 163, 184, 0.12)"
                            t_status_border = "rgba(148, 163, 184, 0.3)"
                            t_card_border = "#64748b"
                            t_val_color = "#cbd5e1"
                        elif latest_score >= 0.5:
                            ticker_status = "BULLISH"
                            t_status_color = "#34d399"
                            t_status_bg = "rgba(16, 185, 129, 0.15)"
                            t_status_border = "rgba(16, 185, 129, 0.35)"
                            t_card_border = "#10b981"
                            t_val_color = "#10b981"
                        else:
                            ticker_status = "BEARISH"
                            t_status_color = "#f87171"
                            t_status_bg = "rgba(239, 68, 68, 0.15)"
                            t_status_border = "rgba(239, 68, 68, 0.35)"
                            t_card_border = "#ef4444"
                            t_val_color = "#ef4444"

                        if abs(delta_idx) < 0.05:
                            delta_tag = '<span style="font-size: 0.64rem; color: var(--text-muted); font-weight: 600; white-space: nowrap;">— No change</span>'
                        elif delta_idx > 0:
                            delta_tag = (
                                f'<span style="font-size: 0.64rem; font-weight: 700; color: #059669; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 1px 4px; border-radius: 3px; font-family: \'Montserrat\', sans-serif; white-space: nowrap; flex-shrink: 0;">▲ {abs(delta_idx):.1f}%</span>'
                                '<span style="font-size: 0.60rem; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">momentum</span>'
                            )
                        else:
                            delta_tag = (
                                f'<span style="font-size: 0.64rem; font-weight: 700; color: #dc2626; background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.25); padding: 1px 4px; border-radius: 3px; font-family: \'Montserrat\', sans-serif; white-space: nowrap; flex-shrink: 0;">▼ {abs(delta_idx):.1f}%</span>'
                                '<span style="font-size: 0.60rem; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">momentum</span>'
                            )

                        kpi_html += (
                            f'<div class="mini-index-card" style="border-left: 3px solid {t_card_border}; margin-bottom: 0;">'
                            '<div style="display: flex; justify-content: space-between; align-items: center; gap: 4px; margin-bottom: 2px; overflow: hidden;">'
                            f'<span style="font-family: \'Montserrat\', sans-serif; font-size: 0.66rem; font-weight: 700; color: #f8fafc; text-transform: uppercase; letter-spacing: -0.02em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{ticker}</span>'
                            f'<span style="font-family: \'Montserrat\', sans-serif; font-size: 0.55rem; font-weight: 800; color: {t_status_color}; background: {t_status_bg}; border: 1px solid {t_status_border}; padding: 0px 3px; border-radius: 3px; letter-spacing: 0; white-space: nowrap; flex-shrink: 0;">{ticker_status}</span>'
                            '</div>'
                            f'<div style="font-family: \'Montserrat\', sans-serif; font-size: clamp(1.15rem, 1.8vw, 1.40rem); font-weight: 800; color: {t_val_color}; margin: 1px 0; line-height: 1.1;">{latest_score:+.1f}</div>'
                            f'<div style="display: flex; align-items: center; justify-content: space-between; gap: 4px; margin-top: 3px; min-width: 0; overflow: hidden;">{delta_tag}</div>'
                            '</div>'
                        )

                    kpi_html += '</div>'
                    st.markdown(kpi_html, unsafe_allow_html=True)
    else:
        st.warning("No data found for the selected parameters.")
