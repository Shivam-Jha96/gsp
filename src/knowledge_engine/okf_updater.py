import os
import asyncio
import logging
import time
import re
import feedparser
from urllib.parse import quote
from google import genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Configure Gemini via the new google.genai SDK
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY environment variable is required.")
    exit(1)

client = genai.Client(api_key=api_key.strip())
# Ordered list of models to try (reliable production models first, followed by fallbacks)
MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-3.7-flash",
    "gemini-2.5-pro",
    "gemini-1.5-pro"
]

# Rate limiting guardrails to stay strictly below Google Gemini 15 RPM free-tier quota
MIN_REQUEST_INTERVAL = 6.0   # Mandatory 6.0s spacing between all API dispatches (<= 10 RPM ceiling)
INTER_REGION_DELAY = 10.0    # 10.0s cooldown between regional runs

_last_request_time = 0.0

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

from config.market_registry import load_market_registry

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
                desc = entry.get("description", "")
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

async def update_region(region_code: str, region_data: dict):
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
    # Try each fallback model with retries
    for model_id in MODEL_FALLBACKS:
        for attempt in range(2):
            try:
                logger.info(f"  Trying model={model_id} (attempt {attempt + 1}/2)...")
                response = await rate_limited_generate(client, model_id, prompt)
                new_content = response.text
                
                if not new_content or len(new_content.strip()) < 80:
                    logger.warning(f"  Empty response from {model_id}, retrying...")
                    await asyncio.sleep(4)
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
                    wait = 12 * (attempt + 1)  # 12s, 24s backoff
                    logger.warning(f"  [QUOTA/429] Rate limit hit on {model_id} (attempt {attempt + 1}/2). Backing off for {wait}s...")
                    await asyncio.sleep(wait)
                elif is_unavailable:
                    wait = 4 * (attempt + 1)  # 4s, 8s backoff
                    logger.warning(f"  [503/UNAVAILABLE] {model_id} busy on Google servers (attempt {attempt + 1}/2). Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                elif is_not_found:
                    logger.warning(f"  [404] {model_id} not found, failing over to next model...")
                    break  # Skip to next model
                else:
                    logger.error(f"  Unexpected error with {model_id}: {e}")
                    break  # Skip to next model

        # Cooldown before switching to next fallback model to avoid immediately hitting project-level quota
        logger.info(f"  Failing over to next fallback model in chain...")
        await asyncio.sleep(3)
    
    logger.error(f"All models failed for {region_data['name']}. OKF not updated.")

async def main():
    logger.info("=== Starting Dynamic OKF Updater ===")
    for region_code, region_data in REGIONS.items():
        await update_region(region_code, region_data)
        logger.info(f"  Cooling down {INTER_REGION_DELAY}s between regions to stay safely under 15 RPM limit...")
        await asyncio.sleep(INTER_REGION_DELAY)
    logger.info("=== OKF Update Complete! ===")

if __name__ == "__main__":
    asyncio.run(main())
