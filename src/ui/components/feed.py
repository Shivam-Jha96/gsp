"""
Live intelligence news feed component: streaming macro headlines, clean summaries, and sentiment pills.
"""

from typing import Optional
import re
import html
import streamlit as st
import pandas as pd

from ui.components.common import make_fragment_decorator, render_segmented_filter

try:
    from ui.state_persistence import sync_preference_to_query_params, get_persisted_feed_index
except Exception:
    try:
        from src.ui.state_persistence import sync_preference_to_query_params, get_persisted_feed_index
    except Exception:
        def sync_preference_to_query_params(*args, **kwargs): pass
        def get_persisted_feed_index(*args, **kwargs): return 0


def clean_news_item(raw_text: str) -> dict:
    """
    Cleans raw RSS event text, strips HTML tags, and extracts headline and publisher source.
    """
    if not raw_text:
        return {"headline": "Market update", "source": ""}
    unescaped = html.unescape(str(raw_text))
    clean = re.sub(r'<[^>]+>', ' ', unescaped)
    clean = re.sub(r'\s+', ' ', clean).strip()

    parts = [p.strip() for p in clean.split(' - ') if p.strip()]
    if not parts:
        return {"headline": clean, "source": ""}

    headline = parts[0]
    source = ""
    if len(parts) > 1:
        for p in reversed(parts[1:]):
            if 1 < len(p) <= 25 and p != headline:
                source = p
                break

    if source and headline.endswith(f" - {source}"):
        headline = headline[:-len(f" - {source}")].strip()

    return {"headline": headline, "source": source}


@make_fragment_decorator(run_every="5m")
def render_live_intelligence_feed(df_payloads: Optional[pd.DataFrame] = None, get_processed_data_fn=None):
    if df_payloads is None and get_processed_data_fn is not None:
        _, df_payloads, _ = get_processed_data_fn()

    if df_payloads is None or df_payloads.empty:
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

    display_payloads = df_payloads[df_payloads['market_region'] == selected_region].copy()

    # --- Timeframe Filtering ---
    if not display_payloads.empty and date_range != "All":
        if display_payloads['timestamp'].dt.tz is None:
            display_payloads['timestamp'] = display_payloads['timestamp'].dt.tz_localize('UTC')

        now = pd.Timestamp.now('UTC')
        cutoff = now
        if date_range in ["4 Hours", "4 Hour", "4H"]: cutoff = now - pd.Timedelta(hours=4)
        elif date_range in ["6 Hours", "6 Hour", "6H"]: cutoff = now - pd.Timedelta(hours=6)
        elif date_range in ["12 Hours", "12 Hour", "12H"]: cutoff = now - pd.Timedelta(hours=12)
        elif date_range in ["1 Day", "1Day", "24 Hours", "24 Hour", "24H"]: cutoff = now - pd.Timedelta(hours=24)
        elif date_range in ["7 Days", "7 Day", "7D"]: cutoff = now - pd.Timedelta(days=7)
        elif date_range in ["1 Month", "1M"]: cutoff = now - pd.Timedelta(days=30)
        elif date_range in ["1 Year", "1Y"]: cutoff = now - pd.Timedelta(days=365)

        display_payloads = display_payloads[display_payloads['timestamp'] >= cutoff]

    if not display_payloads.empty:
        if display_payloads['timestamp'].dt.tz is None:
            display_payloads['timestamp'] = display_payloads['timestamp'].dt.tz_localize('UTC')
        display_payloads['timestamp'] = display_payloads['timestamp'].dt.tz_convert(target_tz)
        display_payloads = display_payloads.sort_values('timestamp', ascending=False)

    region_payloads = display_payloads
    total_events = len(region_payloads)
    bullish_count = int((region_payloads['sentiment_index'] >= 0.5).sum()) if not region_payloads.empty else 0
    bearish_count = int((region_payloads['sentiment_index'] <= -0.5).sum()) if not region_payloads.empty else 0
    neutral_count = total_events - bullish_count - bearish_count

    with st.container(border=True, key="live_intelligence_feed_container"):
        feed_header_col1, feed_header_col2 = st.columns([0.42, 0.58], vertical_alignment="center")
        with feed_header_col1:
            st.markdown(f"""<div style="display: flex; align-items: center; gap: 8px; margin: 0; padding: 0; min-height: 38px;"><span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); flex-shrink: 0;"></span><span style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); font-family: 'Montserrat', sans-serif; line-height: 1.2;">{selected_region} Live Intelligence Feed</span></div>""", unsafe_allow_html=True)
        with feed_header_col2:
            feed_pill_options = [
                f"All {total_events}",
                f"Bullish {bullish_count}",
                f"Bearish {bearish_count}",
                f"Neutral {neutral_count}"
            ]
            default_feed_ix = get_persisted_feed_index(feed_pill_options, default_ix=0)
            selected_feed_pill = render_segmented_filter("feed_filter", feed_pill_options, default_ix=default_feed_ix, key="feed_sentiment_pills")
            if selected_feed_pill:
                pill_prefix = selected_feed_pill.split()[0]
                st.session_state["feed_sentiment_category"] = pill_prefix
                sync_preference_to_query_params("feed", pill_prefix)

        if selected_feed_pill and "Bullish" in selected_feed_pill:
            feed_display_payloads = region_payloads[region_payloads['sentiment_index'] >= 0.5]
            sentiment_label = "Bullish"
        elif selected_feed_pill and "Bearish" in selected_feed_pill:
            feed_display_payloads = region_payloads[region_payloads['sentiment_index'] <= -0.5]
            sentiment_label = "Bearish"
        elif selected_feed_pill and ("Neutral" in selected_feed_pill or "Noise" in selected_feed_pill):
            feed_display_payloads = region_payloads[(region_payloads['sentiment_index'] > -0.5) & (region_payloads['sentiment_index'] < 0.5)]
            sentiment_label = "Neutral"
        else:
            feed_display_payloads = region_payloads
            sentiment_label = "All"

        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 4px 10px 4px; border-bottom: 1px solid var(--feed-card-border); margin-bottom: 10px;">
            <span style="font-size: 0.78rem; font-weight: 700; color: var(--text-secondary); font-family: 'Montserrat', sans-serif; letter-spacing: 0.04em;">
                STREAMING {len(feed_display_payloads)} {sentiment_label.upper()} HEADLINES
            </span>
        </div>
        """, unsafe_allow_html=True)

        html_feed = '<div class="news-feed-scroll">'
        if not feed_display_payloads.empty:
            for _, row in feed_display_payloads.iterrows():
                sentiment = row['sentiment_index']
                if date_range in ["4 Hours", "4 Hour", "4H", "6 Hours", "6 Hour", "6H", "12 Hours", "12 Hour", "12H", "1 Day", "1Day", "1D", "24 Hours", "24 Hour", "24H"]:
                    time_str = pd.to_datetime(row['timestamp']).strftime('%H:%M')
                else:
                    time_str = pd.to_datetime(row['timestamp']).strftime('%b %d, %H:%M')
                ticker_label = row.get('index_ticker', 'Macro')

                parsed = clean_news_item(row['raw_text'])
                clean_headline = parsed['headline']
                source = parsed['source']

                if abs(sentiment) < 0.5:
                    status_badge = '<span style="background: rgba(148, 163, 184, 0.18); border: 1px solid rgba(148, 163, 184, 0.45); color: #cbd5e1; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.06em; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">NEUTRAL</span>'
                    score_color = "#94a3b8"
                    score_bg = "rgba(148, 163, 184, 0.12)"
                    score_border = "rgba(148, 163, 184, 0.3)"
                    card_border = "#64748b"
                elif sentiment >= 0.5:
                    status_badge = '<span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #34d399; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.06em; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">BULLISH</span>'
                    score_color = "#10b981"
                    score_bg = "rgba(16, 185, 129, 0.12)"
                    score_border = "rgba(16, 185, 129, 0.3)"
                    card_border = "#10b981"
                else:
                    status_badge = '<span style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.06em; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">BEARISH</span>'
                    score_color = "#ef4444"
                    score_bg = "rgba(239, 68, 68, 0.12)"
                    score_border = "rgba(239, 68, 68, 0.3)"
                    card_border = "#ef4444"

                source_badge = f'<span style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); color: #94a3b8; padding: 2px 6px; border-radius: 4px; font-size: 0.68rem; font-weight: 600; flex-shrink: 0; font-family: \'Montserrat\', sans-serif;">{source}</span>' if source else ""

                escaped_headline = html.escape(clean_headline)
                badges_markup = (
                    f'<span style="font-family: \'IBM Plex Sans\', sans-serif; font-size: 0.75rem; font-weight: 500; color: #94a3b8; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 2px 7px; border-radius: 4px; flex-shrink: 0;">{time_str}</span>'
                    f'<span style="font-family: \'Montserrat\', sans-serif; font-size: 0.75rem; font-weight: 700; color: #f8fafc; background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.12); padding: 2px 8px; border-radius: 4px; flex-shrink: 0;">{ticker_label}</span>'
                    f'{source_badge}{status_badge}'
                )
                score_markup = f'<div style="flex-shrink: 0;"><span style="font-family: \'Montserrat\', sans-serif; font-size: 0.8rem; font-weight: 700; color: {score_color}; background: {score_bg}; border: 1px solid {score_border}; padding: 3px 9px; border-radius: 4px; letter-spacing: 0.02em;">{sentiment:+.1f}</span></div>'
                card_top = f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;"><div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">{badges_markup}</div>{score_markup}</div>'
                card_body = f'<div style="font-size: 0.92rem; color: #f8fafc; font-weight: 500; line-height: 1.5; font-family: \'IBM Plex Sans\', sans-serif;">{escaped_headline}</div>'

                html_feed += f'<div class="news-item-card" style="border-left: 3px solid {card_border};">{card_top}{card_body}</div>'
        else:
            html_feed += f'<div style="color: var(--text-muted); font-size: 0.88rem; padding: 18px; text-align: center; font-family: \'IBM Plex Sans\', sans-serif;">No news events matching the selected sentiment filter for {selected_region}.</div>'

        html_feed += '</div>'
        st.markdown(html_feed, unsafe_allow_html=True)
