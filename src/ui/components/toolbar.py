"""
Filter toolbar component for cross-regional market selection, timeframe, and EMA parameters.
"""

import streamlit as st
import pandas as pd

from ui.components.common import rerun_scoped


def render_filter_toolbar(df_signals: pd.DataFrame):
    """
    Renders the unified 5-column filter toolbar controlling timeframe, region, chart ticker, timezone, and EMA span.
    """
    with st.container(border=True):
        filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([1.1, 1.25, 1.35, 1.35, 1.05], gap="small")
        lbl_color = "#94a3b8"

        with filter_col1:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 2px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{lbl_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span style="font-size: 0.70rem; font-weight: 700; color: {lbl_color}; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Montserrat', sans-serif;">TIMEFRAME</span>
            </div>
            """, unsafe_allow_html=True)
            timeframe_options = ["7 Days", "1 Day", "12 Hours", "6 Hours", "4 Hours", "1 Month", "1 Year", "All"]
            current_tf = st.session_state.get("filter_timeframe", timeframe_options[0])
            default_tf_ix = timeframe_options.index(current_tf) if current_tf in timeframe_options else 0
            st.selectbox(
                "Timeframe",
                timeframe_options,
                index=default_tf_ix,
                label_visibility="collapsed",
                key="filter_timeframe",
                on_change=lambda: rerun_scoped(["render_analytics_surface", "render_live_intelligence_feed"])
            )

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
                try:
                    from src.config.market_registry import get_all_region_codes
                    all_regions = get_all_region_codes()
                except Exception:
                    all_regions = ["IN", "US", "UK", "JP"]

            available_regions = df_signals['market_region'].unique().tolist() if (df_signals is not None and not df_signals.empty) else []
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
            default_reg_name = region_name_map.get("IN", "India (IN)")
            current_reg = st.session_state.get("filter_region", default_reg_name)
            default_ix = display_regions.index(current_reg) if current_reg in display_regions else (display_regions.index(default_reg_name) if default_reg_name in display_regions else 0)
            st.selectbox(
                "Region",
                display_regions,
                index=default_ix,
                label_visibility="collapsed",
                key="filter_region",
                on_change=lambda: rerun_scoped("app")
            )

        with filter_col3:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 2px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{lbl_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                <span style="font-size: 0.70rem; font-weight: 700; color: {lbl_color}; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Montserrat', sans-serif;">CHART DISPLAY</span>
            </div>
            """, unsafe_allow_html=True)
            selected_region_display = st.session_state.get("filter_region", display_regions[default_ix])
            selected_region = next((code for code, name in region_name_map.items() if name == selected_region_display), selected_region_display)
            if "(" in selected_region_display and ")" in selected_region_display and selected_region not in ["IN", "US", "UK", "JP"]:
                selected_region = selected_region_display.split("(")[-1].replace(")", "").strip()

            active_indices = []
            if df_signals is not None and not df_signals.empty and 'market_region' in df_signals.columns and 'index_ticker' in df_signals.columns:
                active_indices = df_signals[df_signals['market_region'] == selected_region]['index_ticker'].unique().tolist()
                active_indices = [x for x in active_indices if x != 'UNKNOWN']

            chart_options = ["All Indices"] + active_indices
            current_chart = st.session_state.get("filter_chart_display", "All Indices")
            if current_chart not in chart_options:
                current_chart = "All Indices"
                st.session_state["filter_chart_display"] = "All Indices"
            chart_ix = chart_options.index(current_chart) if current_chart in chart_options else 0
            st.selectbox(
                "Chart Display",
                chart_options,
                index=chart_ix,
                label_visibility="collapsed",
                key="filter_chart_display",
                on_change=lambda: rerun_scoped("render_analytics_surface")
            )

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
            base_default_tz_ix = next((i for i, k in enumerate(tz_keys) if "IST" in k), 0)
            current_tz = st.session_state.get("filter_timezone", tz_keys[base_default_tz_ix])
            default_tz_ix = tz_keys.index(current_tz) if current_tz in tz_keys else base_default_tz_ix
            st.selectbox(
                "Timezone",
                tz_keys,
                index=default_tz_ix,
                label_visibility="collapsed",
                key="filter_timezone",
                on_change=lambda: rerun_scoped(["render_header_banner", "render_analytics_surface", "render_live_intelligence_feed"])
            )

        with filter_col5:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 5px; margin-bottom: 2px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{lbl_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                <span style="font-size: 0.70rem; font-weight: 700; color: {lbl_color}; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Montserrat', sans-serif;">EMA WINDOW</span>
            </div>
            """, unsafe_allow_html=True)
            ema_display_options = ["4 Periods", "8 Periods", "12 Periods", "24 Periods"]
            current_ema = st.session_state.get("filter_ema_window", ema_display_options[0])
            default_ema_ix = ema_display_options.index(current_ema) if current_ema in ema_display_options else 0
            st.selectbox(
                "EMA Window",
                ema_display_options,
                index=default_ema_ix,
                label_visibility="collapsed",
                key="filter_ema_window",
                on_change=lambda: rerun_scoped("render_analytics_surface")
            )
