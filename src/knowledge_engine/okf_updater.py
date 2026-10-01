import os
import asyncio
import logging
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
MODEL_ID = "gemini-3.8-flash"

REGIONS = {
    "US": {
        "name": "United States",
        "file": "knowledge/us_macro.okf.md",
        "search_queries": [
            "Federal Reserve interest rate decision",
            "US CPI inflation data",
            "US economy GDP jobs"
        ]
    },
    "IN": {
        "name": "India",
        "file": "knowledge/india_macro.okf.md",
        "search_queries": [
            "Reserve Bank of India RBI repo rate",
            "India inflation CPI data",
            "India economy GDP FPI flows"
        ]
    },
    "UK": {
        "name": "United Kingdom",
        "file": "knowledge/uk_macro.okf.md",
        "search_queries": [
            "Bank of England interest rate decision",
            "UK inflation CPI data",
            "UK economy GDP gilts"
        ]
    },
    "JP": {
        "name": "Japan",
        "file": "knowledge/japan_macro.okf.md",
        "search_queries": [
            "Bank of Japan BOJ interest rate yield curve",
            "Japan inflation CPI yen",
            "Japan economy GDP Nikkei"
        ]
    }
}

def fetch_macro_news(queries: list, max_items_per_query: int = 5) -> str:
    """Fetches recent macroeconomic news from Google News RSS across multiple queries."""
    all_items = []
    seen_titles = set()
    
    for query in queries:
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
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
    
    # 1. Fetch recent macro news from multiple queries
    news_context = fetch_macro_news(region_data["search_queries"])
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
Analyze the latest macroeconomic news to identify any major shifts in Central Bank policy (interest rates, QE/QT), inflation trends, or structural economic shifts.
If the news implies a paradigm shift (e.g. the Central Bank is pivoting from hawkish to dovish), UPDATE the existing rules or ADD new rules to reflect this.
If the news confirms the existing rules, keep them but add more nuance or detail.
Always aim for 4-6 rules per region.

OUTPUT FORMAT:
Output ONLY raw Markdown text. Do NOT wrap it in code blocks.

# {region_data['name']} Macro Trading Rules

## Rule 1: [Rule Name]
- **Condition:** [What happens]
- **Action:** [Market reaction: Bullish on X, Bearish on Y]

(continue for all rules)
"""
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        new_content = response.text
        
        # Strip potential markdown fencing the LLM might hallucinate
        if new_content.startswith("```markdown"):
            new_content = new_content.replace("```markdown", "", 1)
        if new_content.startswith("```"):
            new_content = new_content.replace("```", "", 1)
        if new_content.endswith("```"):
            new_content = new_content[:-3]
            
        # 4. Save to disk
        write_okf(region_data["file"], new_content)
        logger.info(f"Successfully updated {region_data['file']}.")
        
    except Exception as e:
        logger.error(f"Failed to update OKF for {region_data['name']}: {e}")

async def main():
    logger.info("=== Starting Dynamic OKF Updater ===")
    for region_code, region_data in REGIONS.items():
        await update_region(region_code, region_data)
        # Respect 15 RPM rate limit: 60s / 15 = 4s minimum gap
        logger.info("  Waiting 5s for rate limit...")
        await asyncio.sleep(5)
    logger.info("=== OKF Update Complete! ===")

if __name__ == "__main__":
    asyncio.run(main())
