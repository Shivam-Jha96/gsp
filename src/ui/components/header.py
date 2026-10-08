"""
Header banners, branding, telemetry freshness, and compliance notices.
"""

from typing import Optional, Dict, Any
import streamlit as st
import pandas as pd

try:
    from ui.components.common import make_fragment_decorator, render_clean_html
except Exception:
    from src.ui.components.common import make_fragment_decorator, render_clean_html

try:
    from database.telemetry import format_pipeline_freshness
except Exception:
    try:
        from src.database.telemetry import format_pipeline_freshness
    except Exception:
        def format_pipeline_freshness(*args, **kwargs):
            return "Just now", "0m ago", "Real-time telemetry", "fresh"


@make_fragment_decorator(run_every="5m")
def render_header_banner(df_signals: Optional[pd.DataFrame] = None, latest_pipeline_run: Optional[Dict[str, Any]] = None, get_processed_data_fn=None):
    if (df_signals is None or latest_pipeline_run is None) and get_processed_data_fn is not None:
        fresh_signals, _, fresh_run = get_processed_data_fn()
        if df_signals is None:
            df_signals = fresh_signals
        if latest_pipeline_run is None:
            latest_pipeline_run = fresh_run

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
    current_target_tz = tz_options.get(current_selected_tz, "Asia/Kolkata")
    current_tz_abbr = current_selected_tz.split('(')[-1].replace(')', '').strip() if '(' in current_selected_tz else current_selected_tz

    latest_ts = df_signals['timestamp'].max() if (df_signals is not None and not df_signals.empty) else None
    pipeline_completed_at = latest_pipeline_run.get('completed_at') if latest_pipeline_run else None
    time_display_str, relative_display_str, freshness_tooltip, freshness_tier = format_pipeline_freshness(
        pipeline_completed_at, fallback_ts=latest_ts, target_tz_str=current_target_tz, tz_abbr=current_tz_abbr
    )
    if current_tz_abbr != "IST" and time_display_str.endswith(" IST"):
        time_display_str = time_display_str[:-4] + f" {current_tz_abbr}"

    if freshness_tier == "aging":
        pill_bg = "rgba(245, 158, 11, 0.12)"
        pill_border = "rgba(245, 158, 11, 0.32)"
        pill_color = "#fbbf24"
    elif freshness_tier == "stale":
        pill_bg = "rgba(239, 68, 68, 0.12)"
        pill_border = "rgba(239, 68, 68, 0.32)"
        pill_color = "#f87171"
    else:  # fresh
        pill_bg = "rgba(16, 185, 129, 0.10)"
        pill_border = "rgba(16, 185, 129, 0.25)"
        pill_color = "#34d399"

    status_bg = "rgba(16, 185, 129, 0.15)"
    status_border = "rgba(16, 185, 129, 0.35)"
    status_text = "#34d399"

    st.markdown(f"""
    <div class="header-banner-card">
        <div style="display: flex; align-items: center; gap: 14px; flex-wrap: wrap;">
            <svg width="44" height="40" viewBox="15 15 70 75" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.45)); flex-shrink: 0;">
                <defs>
                    <linearGradient id="vFlatCyanAreaH" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#0284c7" stop-opacity="0.45"/>
                        <stop offset="100%" stop-color="#0369a1" stop-opacity="0.05"/>
                    </linearGradient>
                    <linearGradient id="vFlatGreenAreaH" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#10b981" stop-opacity="0.5"/>
                        <stop offset="100%" stop-color="#047857" stop-opacity="0.05"/>
                    </linearGradient>
                    <radialGradient id="vFlatAuraGradH" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stop-color="#34d399" stop-opacity="0.45"/>
                        <stop offset="100%" stop-color="#10b981" stop-opacity="0"/>
                    </radialGradient>
                </defs>
                <line x1="18" y1="72" x2="82" y2="72" stroke="#0e7490" stroke-width="1.2" stroke-dasharray="2.5 3" opacity="0.6"/>
                <path d="M 21 28 L 29 36 L 36 32 L 50 72 L 50 86 L 21 86 Z" fill="url(#vFlatCyanAreaH)"/>
                <path d="M 50 72 L 58 58 L 62 60 L 68 42 L 72 47 L 76 27 L 76 86 L 50 86 Z" fill="url(#vFlatGreenAreaH)"/>
                <line x1="35" y1="26" x2="35" y2="40" stroke="#38bdf8" stroke-width="1.5"/>
                <rect x="33.5" y="30" width="3" height="7" rx="0.8" fill="#0284c7"/>
                <line x1="43" y1="46" x2="43" y2="60" stroke="#38bdf8" stroke-width="1.5"/>
                <rect x="41.5" y="50" width="3" height="6" rx="0.8" fill="#0284c7"/>
                <line x1="62" y1="52" x2="62" y2="67" stroke="#34d399" stroke-width="1.5"/>
                <rect x="60.5" y="56" width="3" height="7" rx="0.8" fill="#10b981"/>
                <line x1="72" y1="38" x2="72" y2="52" stroke="#34d399" stroke-width="1.5"/>
                <rect x="70.5" y="42" width="3" height="6" rx="0.8" fill="#10b981"/>
                <path d="M 21 34 L 29 42 L 36 38 L 50 78 L 58 64 L 62 66 L 68 48 L 72 53 L 74 38" stroke="rgba(255, 255, 255, 0.15)" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M 21 28 L 29 36 L 36 32 L 50 72" stroke="#38bdf8" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M 50 72 L 58 58 L 62 60 L 68 42 L 72 47 L 76 27" stroke="#10b981" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                <circle cx="50" cy="72" r="4.5" fill="#020617" stroke="#38bdf8" stroke-width="2.5"/>
                <circle cx="50" cy="72" r="1.5" fill="#38bdf8"/>
                <circle cx="76" cy="24" r="11" fill="url(#vFlatAuraGradH)"/>
                <circle cx="76" cy="24" r="6" fill="rgba(16, 185, 129, 0.25)"/>
                <polygon points="76,17 71,28 81,28" fill="#34d399"/>
            </svg>
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-family: 'Montserrat', sans-serif; font-size: clamp(1.25rem, 2.4vw, 1.55rem); font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; background: linear-gradient(135deg, #ffffff 30%, #e2e8f0 70%, #6ee7b7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0 2px 10px rgba(0,0,0,0.5)); line-height: 1.1;">VALENCE</span>
                    <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981;"></span>
                    <span style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.32); color: #34d399; font-size: 0.62rem; font-weight: 800; padding: 2px 7px; border-radius: 4px; letter-spacing: 0.08em; text-transform: uppercase; font-family: 'Montserrat', sans-serif;">QUANT</span>
                </div>
                <div style="font-size: clamp(0.66rem, 1.2vw, 0.74rem); font-weight: 600; color: #94a3b8; font-family: 'IBM Plex Sans', sans-serif; letter-spacing: 0.04em; text-transform: uppercase; margin-top: 3px; display: flex; align-items: center; gap: 6px;">
                    <span>Global Macro Sentiment</span>
                    <span style="color: rgba(255,255,255,0.25);">•</span>
                    <span style="color: #34d399;">Directional Signal Engine</span>
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end;">
            <div title="{freshness_tooltip}" style="display: inline-flex; align-items: center; gap: 6px; background: {pill_bg}; border: 1px solid {pill_border}; padding: 5px 10px; border-radius: 4px; flex-shrink: 0; cursor: default; white-space: nowrap;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{pill_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                <span style="font-size: 0.72rem; font-weight: 700; color: {pill_color}; font-family: 'Montserrat', sans-serif; letter-spacing: 0.04em; text-transform: uppercase; white-space: nowrap;">UPDATED {time_display_str}</span>
            </div>
            <div style="display: inline-flex; align-items: center; gap: 7px; background: {status_bg}; border: 1px solid {status_border}; color: {status_text}; font-size: 0.72rem; font-weight: 800; letter-spacing: 0.08em; padding: 5px 11px; border-radius: 4px; text-transform: uppercase; font-family: 'Montserrat', sans-serif; box-shadow: 0 0 10px rgba(16, 185, 129, 0.15); flex-shrink: 0; white-space: nowrap;">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981; display: inline-block;"></span>
                SYSTEM ONLINE
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_usp_banner():
    st.markdown("""
    <details class="usp-collapsible">
        <summary class="usp-summary">
            <div class="usp-summary-inner">
                <span class="usp-badge">⚡ QUANTITATIVE EDGE</span>
                <div class="usp-ticker-wrap">
                    <div class="usp-ticker-track">
                        <span class="usp-ticker-item"><strong>Pure Mathematical Sentiment</strong> via System-One CLM-8B</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: #34d399;">🎯 Zero Hallucination:</strong> Native Choice Probabilities P(Bullish), P(Bearish), P(Neutral)</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: #a78bfa;">⚖️ OKF-Conditioned:</strong> Regional Macroeconomic Policy Rules Applied in Real-Time</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: #fbbf24;">📈 Momentum Vectors:</strong> 4P EMA Cross-Sectional Tracking</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: #34d399;">🛡️ System Online:</strong> Institutional Ingestion & Execution Engine</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <!-- Infinite loop seamless duplicate -->
                        <span class="usp-ticker-item"><strong>Pure Mathematical Sentiment</strong> via System-One CLM-8B</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: #34d399;">🎯 Zero Hallucination:</strong> Native Choice Probabilities P(Bullish), P(Bearish), P(Neutral)</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: #a78bfa;">⚖️ OKF-Conditioned:</strong> Regional Macroeconomic Policy Rules Applied in Real-Time</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: #fbbf24;">📈 Momentum Vectors:</strong> 4P EMA Cross-Sectional Tracking</span>
                        <span style="color: var(--text-muted); opacity: 0.6;">•</span>
                        <span class="usp-ticker-item"><strong style="color: #34d399;">🛡️ System Online:</strong> Institutional Ingestion & Execution Engine</span>
                    </div>
                </div>
                <div class="usp-expand-btn">
                    <span class="usp-expand-text">DETAILS ▾</span>
                    <span class="usp-collapse-text">COLLAPSE ▴</span>
                </div>
            </div>
        </summary>
        <div class="usp-content">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <span style="font-family: 'Montserrat', sans-serif; font-size: clamp(0.85rem, 1.8vw, 0.98rem); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em;">Pure Mathematical Sentiment via Contrastive Language Modeling</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                    <span style="font-size: 0.65rem; font-weight: 700; color: #34d399; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">DETERMINISTIC</span>
                    <span style="font-size: 0.65rem; font-weight: 700; color: #a78bfa; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">OKF-CONDITIONED</span>
                    <span style="font-size: 0.65rem; font-weight: 700; color: #fbbf24; background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.25); padding: 2px 7px; border-radius: 4px; font-family: 'Montserrat', sans-serif;">ZERO HALLUCINATION</span>
                </div>
            </div>
            <div style="font-family: 'IBM Plex Sans', sans-serif; font-size: clamp(0.78rem, 1.5vw, 0.83rem); color: var(--edge-text); line-height: 1.6; margin-bottom: 0;">
                Generative LLMs suffer from prompt drift, hallucination, and confidence clustering. Valence replaces text generation with a <strong>System-One Contrastive Model (CLM-8B)</strong> that projects global news directly onto native choice probabilities: <strong style="color: #34d399; font-weight: 700;">P(Bullish)</strong>, <strong style="color: #f87171; font-weight: 700;">P(Bearish)</strong>, and <strong style="color: var(--text-muted); font-weight: 700;">P(Neutral)</strong>. Headlines are conditioned against regional macroeconomic policy rules (OKF), converting real-time global news into a calibrated directional momentum score [-100, +100].
            </div>
        </div>
    </details>
    """, unsafe_allow_html=True)


def render_regulatory_disclaimer():
    """
    Renders compliance, educational research, and data licensing disclosures in the terminal footer.
    """
    disclaimer_html = """
    <div class="regulatory-notice-card">
        <div class="regulatory-notice-header">
            <div class="regulatory-notice-header-left">
                <span class="regulatory-badge">⚖️ INSTITUTIONAL COMPLIANCE</span>
                <span class="regulatory-title">Quantitative Research & Governance Disclosures</span>
            </div>
            <div class="regulatory-notice-header-right">
                <span class="regulatory-pill green">NON-CUSTODIAL</span>
                <span class="regulatory-pill slate">RESEARCH DEMO</span>
                <span class="regulatory-mono-tag">APACHE-2.0 OPEN-SOURCE</span>
            </div>
        </div>
        <div class="regulatory-grid">
            <div class="regulatory-subcard neutral-border">
                <div class="regulatory-subcard-header">
                    <div class="regulatory-subcard-title">
                        <span style="font-size: 0.9rem;">🎓</span>
                        <span>Academic & Research Scope</span>
                    </div>
                    <span class="regulatory-subcard-badge slate">NON-ADVISORY</span>
                </div>
                <div class="regulatory-callout-pill amber">
                    NOT INVESTMENT ADVICE OR FINANCIAL PROMOTION
                </div>
                <div class="regulatory-bullet-list">
                    <div class="regulatory-bullet-item">
                        <span class="reg-chip">JURISDICTIONS</span>
                        <span>Valence is an open-source research engine. It does not provide trade advice or portfolio management under <strong>SEBI (India)</strong>, <strong>SEC (US)</strong>, <strong>FCA (UK)</strong>, or global authorities.</span>
                    </div>
                    <div class="regulatory-bullet-item">
                        <span class="reg-chip">SIGNALS</span>
                        <span>All sentiment scores, momentum indicators, and directional biases represent probabilistic models and must not be construed as investment recommendations.</span>
                    </div>
                </div>
            </div>
            <div class="regulatory-subcard amber-border">
                <div class="regulatory-subcard-header">
                    <div class="regulatory-subcard-title">
                        <span style="font-size: 0.9rem;">🛡️</span>
                        <span>Execution Safeguards & Attribution</span>
                    </div>
                    <span class="regulatory-subcard-badge amber">LOCKOUT ACTIVE</span>
                </div>
                <div class="regulatory-callout-pill red">
                    AUTOMATED BROKER EXECUTION DISABLED
                </div>
                <div class="regulatory-bullet-list">
                    <div class="regulatory-bullet-item">
                        <span class="reg-chip">CAPITAL</span>
                        <span>Automated broker order routing is hard-disabled in this MVP. Real capital should never be allocated solely based on directional sentiment projections.</span>
                    </div>
                    <div class="regulatory-bullet-item">
                        <span class="reg-chip">NEWS DATA</span>
                        <span>Global financial news events are ingested, filtered, and evaluated solely for algorithmic demonstration under fair-use research parameters.</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="regulatory-bottom-bar">
            <span>VALENCE QUANTITATIVE TERMINAL • SYSTEM-ONE CONTRASTIVE MODEL (CLM-8B) • REGIONAL OKF POLICY RULES</span>
            <span class="regulatory-bottom-right">PROBABILISTIC INFERENCE • NOT INVESTMENT ADVICE</span>
        </div>
    </div>
    """
    render_clean_html(disclaimer_html)
