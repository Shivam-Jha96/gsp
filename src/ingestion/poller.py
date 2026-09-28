import asyncio
import logging
from typing import List, Dict, Any
from .api_clients import RSSClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mocked URLs for global RSS feeds
FEEDS = [
    {"url": "https://finance.yahoo.com/news/rssindex", "region": "US"},
    {"url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "region": "IN"},
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml", "region": "UK"},
    {"url": "https://www.japantimes.co.jp/feed/business/", "region": "JP"}
]

class FeedPoller:
    def __init__(self, feeds: List[Dict[str, str]]):
        self.feeds = feeds
        self.client = RSSClient()

    async def poll_feed(self, feed: Dict[str, str]) -> List[Dict[str, Any]]:
        """Poll a single feed and prepare payloads."""
        url = feed['url']
        region = feed['region']
        
        logger.info(f"Polling feed for region {region}: {url}")
        content = await self.client.fetch_feed(url)
        
        if content:
            parsed_items = self.client.parse_feed(content, region)
            logger.info(f"Retrieved {len(parsed_items)} items from {region}")
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
