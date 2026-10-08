#!/usr/bin/env python3
"""
Valence Operational Health Check & CI Diagnostics Probe.
Monitors:
1. Geotargeted RSS News Feeds across global regions (US, UK, IN, JP).
2. Supabase Connection Pool & Pipeline Telemetry.
3. Modal Serverless CLM-8B Inference Endpoint.

Outputs human-readable diagnostics and appends GitHub Step Summary.
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Set path to resolve src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from config.market_registry import load_market_registry, build_rss_feeds

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ValenceHealthCheck")

HTTP_TIMEOUT = 10.0


def check_rss_feeds() -> List[Dict[str, Any]]:
    """Probes a representative RSS feed for each configured market region."""
    results = []
    feeds = build_rss_feeds()
    
    # Pick one feed per region to keep probe lightweight
    seen_regions = set()
    sampled_feeds = []
    for f in feeds:
        reg = f.get("region")
        if reg not in seen_regions:
            seen_regions.add(reg)
            sampled_feeds.append(f)

    headers = {"User-Agent": "Valence-HealthProbe/1.0 (Institutional Engine; +https://github.com/Shivam-Jha96/gsp)"}

    for feed in sampled_feeds:
        region = feed.get("region", "UNKNOWN")
        url = feed.get("url")
        start_time = time.time()
        try:
            resp = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
            latency_ms = int((time.time() - start_time) * 1000)
            
            if resp.status_code == 200:
                # Basic sanity check for RSS XML content
                has_xml = "<rss" in resp.text[:500].lower() or "<feed" in resp.text[:500].lower() or "<xml" in resp.text[:500].lower()
                status = "HEALTHY" if has_xml else "DEGRADED"
                details = f"HTTP 200 OK ({len(resp.content)} bytes)"
            else:
                status = "FAILED"
                details = f"HTTP {resp.status_code}"
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            status = "FAILED"
            details = str(e)[:80]

        results.append({
            "component": f"RSS Feed ({region})",
            "target": feed.get("name", url)[:30],
            "status": status,
            "latency_ms": latency_ms,
            "details": details
        })

    return results


def check_database() -> Dict[str, Any]:
    """Probes the Supabase connection pool and verifies database responsiveness."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        return {
            "component": "Supabase Pool",
            "target": "PostgreSQL",
            "status": "SKIPPED",
            "latency_ms": 0,
            "details": "DATABASE_URL not set in environment"
        }

    start_time = time.time()
    try:
        from database.client import get_db_client
        client = get_db_client()
        with client.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        latency_ms = int((time.time() - start_time) * 1000)

        # Telemetry check
        from database.telemetry import get_latest_successful_pipeline_run
        latest_run = get_latest_successful_pipeline_run("macro_sentiment_pipeline", db_client=client)
        run_str = latest_run.get("completed_at", "No runs recorded") if latest_run else "No telemetry"

        return {
            "component": "Supabase Pool",
            "target": "Managed Postgres",
            "status": "HEALTHY",
            "latency_ms": latency_ms,
            "details": f"Ping 1 OK (Latest pipeline: {run_str})"
        }
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return {
            "component": "Supabase Pool",
            "target": "Managed Postgres",
            "status": "FAILED",
            "latency_ms": latency_ms,
            "details": str(e)[:80]
        }


def check_inference_endpoint() -> Dict[str, Any]:
    """Probes the serverless Modal Contrastive Language Model endpoint."""
    modal_url = os.environ.get("MODAL_ENDPOINT", "https://shivam-jha96--clm-macro-engine-clm-server.modal.run")
    start_time = time.time()
    try:
        # Send lightweight probe GET
        resp = requests.get(modal_url, timeout=HTTP_TIMEOUT)
        latency_ms = int((time.time() - start_time) * 1000)
        # Any non-5xx response indicates the Modal container server is routing traffic
        if resp.status_code < 500:
            status = "HEALTHY"
            details = f"HTTP {resp.status_code} (Reachable)"
        else:
            status = "DEGRADED"
            details = f"HTTP {resp.status_code}"
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        status = "DEGRADED"
        details = str(e)[:80]

    return {
        "component": "Modal CLM-8B Inference",
        "target": modal_url[:35] + "...",
        "status": status,
        "latency_ms": latency_ms,
        "details": details
    }


def generate_markdown_report(checks: List[Dict[str, Any]]) -> str:
    """Formats health probe results into a clean GitHub Actions Markdown summary."""
    status_icons = {
        "HEALTHY": "🟢 Healthy",
        "DEGRADED": "🟡 Degraded",
        "SKIPPED": "⚪ Skipped",
        "FAILED": "🔴 Failed"
    }

    lines = [
        "## 🛡️ Valence Operational Health Probe",
        "",
        f"**Timestamp (UTC):** `{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}`",
        "",
        "| Component | Target | Status | Latency | Details |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]

    for c in checks:
        icon_status = status_icons.get(c['status'], c['status'])
        lines.append(f"| {c['component']} | `{c['target']}` | {icon_status} | {c['latency_ms']}ms | {c['details']} |")

    lines.append("")
    overall_ok = all(c['status'] in ("HEALTHY", "SKIPPED") for c in checks)
    if overall_ok:
        lines.append("> 🚀 **All primary services operational. Institutional pipeline ready.**")
    else:
        lines.append("> ⚠️ **One or more subsystems require attention. Check logs for details.**")
    lines.append("")

    return "\n".join(lines)


def main():
    logger.info("Starting Valence Operational Health Probe...")
    all_checks: List[Dict[str, Any]] = []

    # 1. RSS feeds
    rss_checks = check_rss_feeds()
    all_checks.extend(rss_checks)

    # 2. Database pool
    db_check = check_database()
    all_checks.append(db_check)

    # 3. Modal CLM inference endpoint
    inf_check = check_inference_endpoint()
    all_checks.append(inf_check)

    # Generate Report
    report = generate_markdown_report(all_checks)
    print("\n" + report + "\n")

    # If in GitHub Actions, write to summary
    gh_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh_summary_file:
        try:
            with open(gh_summary_file, "a", encoding="utf-8") as f:
                f.write(report + "\n")
            logger.info("Successfully appended health report to GITHUB_STEP_SUMMARY.")
        except Exception as e:
            logger.warning(f"Could not write to GITHUB_STEP_SUMMARY: {e}")

    # Determine exit code: RSS feeds are critical.
    rss_failures = [c for c in rss_checks if c['status'] == 'FAILED']
    if len(rss_failures) >= len(rss_checks):
        logger.error("All regional RSS feeds failed.")
        sys.exit(1)

    logger.info("Health probe completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
