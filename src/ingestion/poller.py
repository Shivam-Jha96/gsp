import asyncio
import logging
from typing import List, Dict, Any
from .api_clients import RSSClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Institutional Market Indices for Global Regions
FEEDS = [
    # United States (US)
    {"url": "https://news.google.com/rss/search?q=S%26P+500+market", "region": "US", "ticker": "S&P 500"},
    {"url": "https://news.google.com/rss/search?q=NASDAQ+market", "region": "US", "ticker": "NASDAQ"},
    {"url": "https://news.google.com/rss/search?q=Dow+Jones+market", "region": "US", "ticker": "Dow Jones"},
    {"url": "https://news.google.com/rss/search?q=Russell+2000+market", "region": "US", "ticker": "Russell 2000"},
    {"url": "https://news.google.com/rss/search?q=VIX+volatility+index", "region": "US", "ticker": "VIX"},
    
    # India (IN)
    {"url": "https://news.google.com/rss/search?q=Nifty+50+market", "region": "IN", "ticker": "Nifty 50"},
    {"url": "https://news.google.com/rss/search?q=Sensex+market", "region": "IN", "ticker": "Sensex"},
    {"url": "https://news.google.com/rss/search?q=Nifty+Bank+index", "region": "IN", "ticker": "Nifty Bank"},
    {"url": "https://news.google.com/rss/search?q=Nifty+IT+index", "region": "IN", "ticker": "Nifty IT"},
    {"url": "https://news.google.com/rss/search?q=BSE+Midcap+market", "region": "IN", "ticker": "BSE Midcap"},

    # United Kingdom (UK)
    {"url": "https://news.google.com/rss/search?q=FTSE+100+market", "region": "UK", "ticker": "FTSE 100"},
    {"url": "https://news.google.com/rss/search?q=FTSE+250+market", "region": "UK", "ticker": "FTSE 250"},
    {"url": "https://news.google.com/rss/search?q=FTSE+All-Share", "region": "UK", "ticker": "FTSE All-Share"},
    {"url": "https://news.google.com/rss/search?q=FTSE+AIM+UK", "region": "UK", "ticker": "FTSE AIM"},
    {"url": "https://news.google.com/rss/search?q=UK+Gilt+Yields", "region": "UK", "ticker": "UK Gilts"},
    
    # Japan (JP)
    {"url": "https://news.google.com/rss/search?q=Nikkei+225+market", "region": "JP", "ticker": "Nikkei 225"},
    {"url": "https://news.google.com/rss/search?q=TOPIX+index", "region": "JP", "ticker": "TOPIX"},
    {"url": "https://news.google.com/rss/search?q=Mothers+Index+Japan", "region": "JP", "ticker": "JP Mothers"},
    {"url": "https://news.google.com/rss/search?q=JASDAQ+market", "region": "JP", "ticker": "JASDAQ"},
    {"url": "https://news.google.com/rss/search?q=JGB+Yields+Japan", "region": "JP", "ticker": "JP Bonds"}
]

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
