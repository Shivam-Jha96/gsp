---
last_mapped_commit: cf96f4d0048d4bf12ec1ec9d2a683bd1077373a2
last_mapped_at: 2026-10-05
---
# Technical Concerns & Areas of Attention

**Analysis Date:** 2026-10-05

## Technical Debt & Fragile Areas

**1. Streamlit Version Compatibility & DOM Selectors (`src/ui/app.py`):**
- **Issue:** Modern Streamlit versions (1.40+ through 1.65+) have phased out legacy DOM wrapper elements such as `[data-testid="stVerticalBlockBorderWrapper"]` in favor of directly styling `stVerticalBlock`.
- **Impact:** Custom CSS relying solely on legacy testids will fail to apply padding, background, or spacing overrides, resulting in layout shifts or excess padding (as observed in recent feed container spacing fixes).
- **Mitigation:** Use explicit widget/container keys (`key="live_intelligence_feed_container"`) which generate reliable, deterministic CSS classes (`.st-key-<key>`) that survive Streamlit frontend refactors.

**2. Hardcoded Data Cutoff Floor (`src/ui/app.py`):**
- **Issue:** Line 1190 sets an explicit cutoff floor: `DATA_CUTOFF_FLOOR = pd.Timestamp("2026-09-30 06:30:00", tz="UTC")` to purge historical data distorted by an early rubric bug.
- **Risk:** In long-running deployments, this filter remains in memory. While harmless for current data, it represents a hardcoded historical patch that should eventually be superseded by clean database state.

**3. Single-File UI Monolith (`src/ui/app.py`):**
- **Issue:** `src/ui/app.py` is currently ~1,880 lines, housing theme variables, comprehensive CSS injection, data retrieval, regional gatekeeping, layout rendering, Plotly chart generation, mini KPI cards, and news feed streaming.
- **Risk:** Context overhead and increased risk of merge conflicts or accidental styling regression during updates.
- **Recommendation:** Refactor into modular components under `src/ui/components/` (e.g. `header.py`, `toolbar.py`, `chart.py`, `feed.py`, `styles.py`).

## External API & Dependency Risks

**1. Remote Supabase Pooler Idle Timeouts:**
- **Issue:** Managed cloud PostgreSQL poolers drop idle connections without sending TCP FIN packets, resulting in `OperationalError: SSL SYSCALL error: EOF detected` when an idle connection is checked out.
- **Current State:** Mitigated by `SupabasePoolClient` with `_is_alive(conn)` pre-flight validation and pool auto-resetting, but long-lived worker threads must maintain proper connection disposal.

**2. Google Gemini Free-Tier Quota Ceiling (15 RPM):**
- **Issue:** The automated OKF rule updater (`src/knowledge_engine/okf_updater.py`) runs against Gemini APIs that impose strict 15 RPM / 1M TPM quotas on free tiers.
- **Current State:** Mitigated by rate pacing (`MIN_REQUEST_INTERVAL = 6.0s`) and multi-pass model fallback pools. If multiple GitHub Actions workflows trigger simultaneously, quota contention could occur.

**3. TypeSafe / Modal Serverless Cold Starts:**
- **Issue:** The Contrastive Language Model (CLM-8B) is hosted as a serverless container on Modal. If cold, the initial request in a batch could take 15–30 seconds to initialize GPU memory before processing headlines.
- **Current State:** Handled by generous client timeouts (`timeout=120.0s`), but cold starts slightly delay scheduled ingestion runs.

## Security & Operational Practices

**1. Secret Management:**
- Database credentials, Modal API keys, and Alpaca secrets must never be committed to repository files.
- All secrets are properly loaded via environment variables (`DATABASE_URL`, `TYPESAFE_API_KEY`, `GEMINI_API_KEY`, `ALPACA_API_KEY`).

**2. RSS Feed Dependability:**
- Ingestion relies on public Google News RSS queries. While resilient and regionalized with geotargeted parameters (`gl`, `hl`, `ceid`), upstream schema alterations or aggressive IP rate-limiting by search engines could impact feed freshness.

---

*Concerns analysis: 2026-10-05*
*Update as technical debt is addressed or new risks emerge*
