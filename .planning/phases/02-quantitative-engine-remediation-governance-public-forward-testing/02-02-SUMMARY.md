---
phase: 02
plan: 02
title: Pipeline Hardening, Model Fallback Registry & OKF Governance
status: completed
date: 2026-10-08
key_files:
  created:
    - scripts/add_audit_columns.sql
  modified:
    - src/knowledge_engine/okf_updater.py
    - .github/workflows/update_okf.yml
    - src/database/schemas.sql
    - src/main.py
---

# Summary 02-02: Pipeline Hardening, Model Fallback Registry & OKF Governance

## What Changed
1. **`src/knowledge_engine/okf_updater.py`**:
   - Replaced retired `gemini-1.5/2.0-flash` with active models: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3.x-flash`.
   - Added `validate_macro_rule_diff()` protecting against macro rule wipeout / shrink > 35%.
2. **`.github/workflows/update_okf.yml`**:
   - Replaced direct `git push origin master` with automated PR creation using `peter-evans/create-pull-request@v6`.
   - Added `pull-requests: write` permissions and `okf-update/` branch naming.
3. **`src/database/schemas.sql` & `scripts/add_audit_columns.sql`**:
   - Added audit columns to `event_signals`: `published_at`, `scored_at`, `okf_version_hash`, `model_version`.
   - Created standalone migration script for existing deployments.
4. **`src/main.py`**:
   - Extracted `published_at` from news metadata, tracked `scored_at`, recorded OKF commit hash, and identified inference model.
   - Implemented resilient insert with backward-compatible legacy fallback if target database has not run the migration script.
