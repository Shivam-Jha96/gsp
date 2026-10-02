---
name: gsp-doc-sync
description: >-
  Synchronizes and updates the Global Sentiment Platform (GSP) documentation suite
  (README.md, docs/sentiment_math.md, docs/architecture_and_workflow.md, and mvp_workflow.md artifact)
  whenever new features, AI inference logic, scoring math, ingestion feeds, database schemas,
  or UI components are modified.
---

# GSP Documentation Suite Synchronization Skill

## Overview
This skill provides the operational protocol for keeping the **Global Macro-Sentiment Tracker (GSP)** documentation suite strictly synchronized with ongoing code, mathematical formulation, and infrastructure changes.

Whenever a change is introduced to the codebase, the agent must evaluate the impact across the four primary documentation assets:
1. **Root Readme**: [`README.md`](../../README.md) (Executive overview, USP, high-level math, getting started)
2. **Mathematical Formulation**: [`docs/sentiment_math.md`](../../docs/sentiment_math.md) (Rigorous quant proofs, softmax derivations, worked numerical examples)
3. **System Architecture**: [`docs/architecture_and_workflow.md`](../../docs/architecture_and_workflow.md) (7-tier architecture, sequence flows, infra SLA matrix, operational runbooks)
4. **Persistent Artifact**: [`mvp_workflow.md`](C:/Users/Lenovo/.gemini/antigravity/brain/6ef3d206-738e-47fe-acdb-a38de79ed13c/mvp_workflow.md) (End-to-end execution workflow tracking active phase deliverables)

---

## Code-to-Document Impact Matrix

Use this matrix to identify which documents must be updated based on modified source files:

| Modified Source Files | Primary Responsibilities | Impacted Documentation |
| :--- | :--- | :--- |
| `src/ai_engine/`, `src/main.py` (Inference logic, scoring math) | System-One CLM, probabilities, relative spread, magnitude, model IDs | `README.md` (USP & Math summary)<br>`docs/sentiment_math.md` (Full derivation & proofs)<br>`docs/architecture_and_workflow.md` (Layer 2)<br>`mvp_workflow.md` (Section 3) |
| `src/ingestion/` (`poller.py`, `api_clients.py`) | RSS sources, Google News/Reuters queries, ticker lists, rate limits | `README.md` (Core Components)<br>`docs/architecture_and_workflow.md` (Layer 1)<br>`mvp_workflow.md` (Section 2) |
| `src/database/` (`schemas.sql`, `client.py`) | Supabase schemas, vertical partitioning, indexing, pooler config | `docs/architecture_and_workflow.md` (Layer 3 & Runbooks)<br>`mvp_workflow.md` (Section 4) |
| `src/signal_engine/` (`ema.py`, `cron_jobs.py`) | EMA periods, cross-sectional aggregation, Alpaca paper trading | `docs/sentiment_math.md` (EMA formulation)<br>`docs/architecture_and_workflow.md` (Layer 4)<br>`mvp_workflow.md` (Section 5) |
| `src/ui/` (`app.py`) | Streamlit layout, Plotly area charts, timezones, KPI tiles, calibration | `docs/architecture_and_workflow.md` (Layer 5)<br>`mvp_workflow.md` (Section 6) |
| `src/knowledge_engine/`, `knowledge/*.okf.md` | Daily OKF updates, Gemini prompt rules, fallback chains | `docs/architecture_and_workflow.md` (Layer 6)<br>`mvp_workflow.md` (Section 7) |
| `.github/workflows/` (`deploy.yml`, `update_okf.yml`, etc.) | Cron schedules, runner dependencies, CI triggers, secrets | `README.md` (CI/CD table)<br>`docs/architecture_and_workflow.md` (Layer 7) |

---

## Step-by-Step Execution Workflow

### Step 1: Detect Code Changes & Audit Scope
Run `git diff --stat HEAD~1` or inspect uncommitted changes in the working tree to determine which tiers were touched.

```bash
git status --short
git diff --stat
```

### Step 2: Synchronize Target Documents

#### A. Updating Mathematical Formulations (`docs/sentiment_math.md`)
When altering sentiment scoring equations:
1. Update the **Tri-Partite Probability Extraction** section if softmax, temperature $\tau$, or projection head dimensions change.
2. Update the **Relative Directional Conviction ($S_{\text{rel}}$)** formula:
   $$S_{\text{rel}} = \frac{P(\text{Bullish}) - P(\text{Bearish})}{P(\text{Bullish}) + P(\text{Bearish}) + \epsilon}$$
3. Update the **Conviction & Neutral Attenuation Magnitude ($M$)**:
   $$M = |S_{\text{rel}}| \times \left(1.0 - 0.5 \times P(\text{Neutral})\right)$$
4. Update the **Worked Numerical Examples** in Section 9 to ensure all 4-decimal step-by-step arithmetic matches the updated code logic.
5. Verify KaTeX formatting: Ensure inline math uses single `$` and display equations use `$$`.

#### B. Updating System Architecture (`docs/architecture_and_workflow.md`)
When modifying infrastructure, workflows, or layer implementations:
1. Update the **Mermaid Flowchart** in Section 2 if nodes, connections, or dataflows change.
2. Update the corresponding tier in the **Layer-by-Layer Technical Breakdown** (Section 3).
3. If new third-party services, APIs, or infrastructure components are introduced, add them to the **Infrastructure & Service Dependency Matrix** (Section 4).
4. If new failure modes or recovery mechanisms are introduced, add corresponding runbooks to **Production Operations & Troubleshooting Guide** (Section 5).

#### C. Updating Root [`README.md`](../../README.md)
1. Keep the **USP Section** synchronized with current model capabilities and performance metrics (latency, determinism, cost).
2. Keep the **Mathematical Scoring Formulation** flowchart and 5-stage summary aligned with `docs/sentiment_math.md`.
3. Keep the **Repository Structure** file tree aligned with actual directory layouts.
4. Ensure cross-reference links (`docs/sentiment_math.md` and `docs/architecture_and_workflow.md`) remain valid.

#### D. Updating Persistent Artifact (`mvp_workflow.md`)
1. Update the brain artifact at `<appDataDir>/brain/<conversation-id>/mvp_workflow.md`.
2. Ensure the active Phase MVP specifications reflect current implementation reality.

---

### Step 3: Verification & Quality Assurance
1. **Cross-Check Equation Variables**: Ensure variable names ($S_{\text{rel}}$, $M$, $I_t$, $\alpha$, $W$) are identical across `README.md`, `sentiment_math.md`, `architecture_and_workflow.md`, and `src/main.py`.
2. **Verify File Links**: Check that all relative and absolute GitHub markdown links point to existing source files.
3. **Compile Python Code**: Confirm code modified alongside docs compiles without errors:
   ```bash
   python -m py_compile src/main.py src/ui/app.py
   ```
4. **Git Tracking Check**: Ensure `docs/` is tracked and not inadvertently ignored in `.gitignore`.

---

### Step 4: Commit and Push
Commit all synchronized documentation changes together with code modifications or as a dedicated documentation revision:

```bash
git add README.md docs/ .agents/
git commit -m "docs: sync architecture, math formulations, and root readme with recent changes"
git push origin master
```
