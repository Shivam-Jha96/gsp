import os
import asyncio
import logging
import time
import re
import feedparser
from urllib.parse import quote
from google import genai
from config.market_registry import load_market_registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Default model fallback priority list
DEFAULT_MODEL_FALLBACKS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

# Rate limiting guardrails to stay strictly below Google Gemini 15 RPM free-tier quota
MIN_REQUEST_INTERVAL = 6.0   # Mandatory 6.0s spacing between all API dispatches (<= 10 RPM ceiling)
INTER_REGION_DELAY = 10.0    # 10.0s cooldown between regional runs

_last_request_time = 0.0

def get_available_models(client) -> list:
    """
    Discovers available Gemini models dynamically from the Google GenAI API
    to eliminate 404 errors caused by deprecated model IDs or account tier constraints.
    """
    preferred_priority = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]
    discovered = []
    try:
        pager = client.models.list()
        for m in pager:
            name = getattr(m, "name", "") or ""
            name = name.replace("models/", "")
            actions = getattr(m, "supported_actions", []) or []
            if name and ("generateContent" in actions or not actions):
                discovered.append(name)
        logger.info(f"Dynamically discovered {len(discovered)} available Gemini models in account: {discovered[:10]}")
    except Exception as e:
        logger.warning(f"Unable to query client.models.list(): {e}. Using static fallbacks.")
        return DEFAULT_MODEL_FALLBACKS

    # Prioritize preferred models if discovered
    models_to_use = [m for m in preferred_priority if m in discovered]
    # Add any other discovered flash models
    for m in discovered:
        if "flash" in m.lower() and m not in models_to_use:
            models_to_use.append(m)
    # Add pro models as final resilience tier
    for m in discovered:
        if "pro" in m.lower() and m not in models_to_use:
            models_to_use.append(m)

    if not models_to_use:
        models_to_use = DEFAULT_MODEL_FALLBACKS

    logger.info(f"Active resilient model priority: {models_to_use}")
    return models_to_use

async def rate_limited_generate(client, model_id: str, prompt: str):
    """
    Enforces a mandatory 6.0-second floor between any two Gemini API calls,
    preventing RPM bursts regardless of retries or fallback switching.
    """
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_INTERVAL:
        sleep_needed = MIN_REQUEST_INTERVAL - elapsed
        logger.info(f"  [RATE-GUARD] Pacing dispatch: waiting {sleep_needed:.2f}s to strictly preserve 15 RPM quota...")
        await asyncio.sleep(sleep_needed)
        
    response = client.models.generate_content(
        model=model_id,
        contents=prompt
    )
    _last_request_time = time.time()
    return response

# Dynamically loaded from declarative market registry
_REGISTRY = load_market_registry()
REGIONS = {
    code: {
        "name": meta["name"],
        "file": meta["okf_file"],
        "search_queries": meta.get("macro_queries", []),
        "locale": meta.get("locale", {"hl": "en-US", "gl": "US", "ceid": "US:en"})
    }
    for code, meta in _REGISTRY.items()
}

def fetch_macro_news(queries: list, locale: dict = None, max_items_per_query: int = 5) -> str:
    """Fetches recent macroeconomic news from Google News RSS across multiple queries with regional geotargeting."""
    all_items = []
    seen_titles = set()
    
    hl = locale.get("hl", "en-US") if locale else "en-US"
    gl = locale.get("gl", "US") if locale else "US"
    ceid = locale.get("ceid", "US:en") if locale else "US:en"
    
    for query in queries:
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={hl}&gl={gl}&ceid={ceid}"
        
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_items_per_query]:
            title = entry.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                all_items.append(f"- {title}")
    
    logger.info(f"  Fetched {len(all_items)} unique news items.")
    return "\n".join(all_items)

def read_current_okf(filepath: str) -> str:
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "No existing rules found."

def write_okf(filepath: str, content: str):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

async def update_region(region_code: str, region_data: dict, client, model_fallbacks: list):
    logger.info(f"Updating OKF for {region_data['name']} ({region_code})...")
    
    # 1. Fetch recent macro news from multiple queries (geotargeted)
    news_context = fetch_macro_news(region_data["search_queries"], locale=region_data.get("locale"))
    if not news_context:
        logger.warning(f"No news found for {region_data['name']}, skipping.")
        return
        
    # 2. Read existing rules
    current_rules = read_current_okf(region_data["file"])
    
    # 3. Ask Gemini to analyze and update
    prompt = f"""You are an elite quantitative macroeconomist updating the Objective Knowledge Framework (OKF) trading rules for the {region_data['name']} market.

CURRENT OKF RULES:
{current_rules}

LATEST MACROECONOMIC NEWS:
{news_context}

TASK:
1. Analyze the latest macroeconomic news to identify any major shifts in Central Bank policy (interest rates, QE/QT), inflation trends, sovereign debt & yield curves, currency dynamics, trade tariffs, commodities, or structural economic shifts.
2. Maintain comprehensive coverage across all active, distinct macroeconomic transmission channels for this region:
   - Monetary Policy & Liquidity (Interest rates, QE/QT, banking reserve ratios)
   - Inflation Dynamics (Core vs. headline, wage pressure, supply bottlenecks)
   - Sovereign Debt & Fiscal Policy (Yield curves, deficit expansion, bond issuance)
   - Currency & External Balance (FX depreciation/appreciation, central bank intervention)
   - Trade, Tariffs & Geopolitical Friction (Import/export levies, sanctions, supply chains)
   - Commodity & Energy Dynamics (Crude oil, food baskets, monsoon/agricultural cycles)
   - Capital Flows & Institutional Liquidity (FPI/FII flows, credit spreads, corporate earnings)
   - Structural & Secular Drivers (Technology/AI investment, corporate governance reforms)
3. DO NOT artificially restrict or cap the number of rules. Generate as many rules as necessary to fully capture the active macroeconomic landscape without arbitrary ceilings.
4. Ensure each rule is mutually exclusive, concise, and institutional-grade:
   - Keep Conditions focused on clear catalysts, economic thresholds, or policy triggers (1-2 sentences).
   - Keep Actions focused on direct directional market reactions: Bullish on Asset A, Bearish on Asset B.
5. If the news implies a paradigm shift (e.g. Central Bank pivot, new tariff regime), update or add rules to reflect this. If existing rules are confirmed or unchanged, preserve them with necessary nuance. Prune any truly obsolete or superseded rules, but never discard an active transmission channel just to meet a target count.

OUTPUT FORMAT:
Output ONLY raw Markdown text. Do NOT wrap it in code blocks.

# {region_data['name']} Macro Trading Rules

## Rule 1: [Rule Name]
- **Condition:** [What happens]
- **Action:** [Market reaction: Bullish on X, Bearish on Y]

(continue for all rules)
"""
    # Up to 2 passes across candidate models to absorb transient Google 503 bursts
    for pass_num in range(1, 3):
        for model_id in model_fallbacks:
            try:
                logger.info(f"  [Pass {pass_num}] Trying model={model_id}...")
                response = await rate_limited_generate(client, model_id, prompt)
                new_content = response.text
                
                if not new_content or len(new_content.strip()) < 80:
                    logger.warning(f"  Empty response from {model_id}, trying next model...")
                    continue

                # Strip potential markdown fencing the LLM might hallucinate
                new_content = re.sub(r"^```(?:markdown)?\s*", "", new_content.strip(), flags=re.IGNORECASE)
                new_content = re.sub(r"\s*```$", "", new_content)
                    
                # Save to disk
                write_okf(region_data["file"], new_content)
                logger.info(f"Successfully updated {region_data['file']} using {model_id}.")
                return  # Success, exit the function
                
            except Exception as e:
                error_str = str(e)
                error_upper = error_str.upper()
                is_rate_limit = any(k in error_upper for k in ["429", "RESOURCE_EXHAUSTED", "RATE_LIMIT", "QUOTA"])
                is_unavailable = any(k in error_upper for k in ["503", "UNAVAILABLE", "OVERLOADED"])
                is_not_found = "404" in error_upper or "NOT_FOUND" in error_upper

                if is_rate_limit:
                    logger.warning(f"  [QUOTA/429] Rate limit hit on {model_id}. Cooling down 8s before trying next model...")
                    await asyncio.sleep(8)
                elif is_unavailable:
                    # 503 means this specific model cluster is busy; failover IMMEDIATELY to next model in pool without wasted sleep loops
                    logger.warning(f"  [503/UNAVAILABLE] {model_id} busy on Google servers. Failing over immediately to next model in pool...")
                    await asyncio.sleep(2)
                elif is_not_found:
                    logger.warning(f"  [404] {model_id} not found on this API endpoint. Skipping...")
                else:
                    logger.error(f"  Unexpected error with {model_id}: {e}. Skipping to next fallback...")
                    await asyncio.sleep(2)

        if pass_num == 1:
            logger.warning(f"All candidate models busy or transiently failed for {region_data['name']} in Pass 1. Cooldown 10s before Pass 2...")
            await asyncio.sleep(10)
    
    logger.error(f"All models exhausted after 2 passes for {region_data['name']}. Existing OKF rules preserved.")

async def main():
    logger.info("=== Starting Dynamic OKF Updater ===")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is required.")
        exit(1)

    client = genai.Client(api_key=api_key.strip())
    model_fallbacks = get_available_models(client)

    for region_code, region_data in REGIONS.items():
        await update_region(region_code, region_data, client, model_fallbacks)
        logger.info(f"  Cooling down {INTER_REGION_DELAY}s between regions to stay safely under 15 RPM limit...")
        await asyncio.sleep(INTER_REGION_DELAY)
    logger.info("=== OKF Update Complete! ===")

if __name__ == "__main__":
    asyncio.run(main())
