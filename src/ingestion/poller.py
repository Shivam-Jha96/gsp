import asyncio
import logging
from typing import List, Dict, Any
from .api_clients import RSSClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base tracking queries for global indices
BASE_QUERIES = [
    # United States (US)
    ("US", "S&P 500", "S%26P+500+market"),
    ("US", "NASDAQ", "NASDAQ+market"),
    ("US", "Dow Jones", "Dow+Jones+market"),
    ("US", "Russell 2000", "Russell+2000+market"),
    ("US", "VIX", "VIX+volatility+index"),
    
    # India (IN)
    ("IN", "Nifty 50", "Nifty+50+market"),
    ("IN", "Sensex", "Sensex+market"),
    ("IN", "Nifty Bank", "Nifty+Bank+index"),
    ("IN", "Nifty IT", "Nifty+IT+index"),
    ("IN", "BSE Midcap", "BSE+Midcap+market"),

    # United Kingdom (UK)
    ("UK", "FTSE 100", "FTSE+100+market"),
    ("UK", "FTSE 250", "FTSE+250+market"),
    ("UK", "FTSE All-Share", "FTSE+All-Share"),
    ("UK", "FTSE AIM", "FTSE+AIM+UK"),
    ("UK", "UK Gilts", "UK+Gilt+Yields"),
    
    # Japan (JP)
    ("JP", "Nikkei 225", "Nikkei+225+market"),
    ("JP", "TOPIX", "TOPIX+index"),
    ("JP", "JP Mothers", "Mothers+Index+Japan"),
    ("JP", "JASDAQ", "JASDAQ+market"),
    ("JP", "JP Bonds", "JGB+Yields+Japan")
]

# Dynamically generate FEEDS to include both General News and Reuters-specific news
FEEDS = []
for region, ticker, query in BASE_QUERIES:
    # 1. General Global News Aggregation
    FEEDS.append({
        "url": f"https://news.google.com/rss/search?q={query}",
        "region": region, 
        "ticker": ticker
    })
    # 2. Strict Reuters-Only Aggregation
    FEEDS.append({
        "url": f"https://news.google.com/rss/search?q={query}+site:reuters.com",
        "region": region, 
        "ticker": ticker
    })

class FeedPoller:
    def __init__(self, feeds: List[Dict[str, str]]):
        self.feeds = feeds
        self.client = RSSClient()

    async def poll_feed(self, feed: Dict[str, str]) -> List[Dict[str, Any]]:
        """Poll a single feed and prepare payloads."""
        url = feed['url']
        region = feed['region']
        ticker = feed.get('ticker', 'UNKNOWN')
        
        logger.info(f"Polling feed for [{region}] {ticker}: {url}")
        content = await self.client.fetch_feed(url)
        
        if content:
            parsed_items = self.client.parse_feed(content, region)
            # Inject ticker into the payload metadata
            for item in parsed_items:
                item['index_ticker'] = ticker
                
            logger.info(f"Retrieved {len(parsed_items)} items for {ticker}")
            return parsed_items
        return []

    def prepare_payloads(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare payloads to be sent to the AI Engine."""
        payloads = []
        for item in items:
            # Transform or enrich data as required by the AI engine
            payload = {
                "source_system": "RSS_POLLER",
                "content_type": "news",
                "region_tag": item["market_region"],
                "index_ticker": item.get("index_ticker", "UNKNOWN"),
                "data": {
                    "headline": item["title"],
                    "summary": item["description"],
                    "url": item["link"],
                    "timestamp": item["published_at"]
                }
            }
            payloads.append(payload)
        return payloads

    async def run(self):
        """Run the poller for all configured feeds."""
        logger.info("Starting ingestion poller...")
        tasks = [self.poll_feed(feed) for feed in self.feeds]
        results = await asyncio.gather(*tasks)
        
        # Flatten the list of lists
        all_items = [item for sublist in results for item in sublist]
        
        # Prepare payloads for the AI Engine
        payloads = self.prepare_payloads(all_items)
        
        logger.info(f"Prepared {len(payloads)} total payloads for the AI Engine.")
        
        return payloads

if __name__ == "__main__":
    poller = FeedPoller(feeds=FEEDS)
    asyncio.run(poller.run())
