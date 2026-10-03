import asyncio
import logging
from typing import List, Dict, Any
from .api_clients import RSSClient
from .classifier import RegionalAffinityClassifier
from config.market_registry import build_rss_feeds

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dynamically generated from the declarative market registry with geotargeting and exact quotes
FEEDS = build_rss_feeds()

class FeedPoller:
    def __init__(self, feeds: List[Dict[str, str]] = None):
        self.feeds = feeds if feeds is not None else FEEDS
        self.client = RSSClient()
        self.classifier = RegionalAffinityClassifier()

    async def poll_feed(self, feed: Dict[str, str]) -> List[Dict[str, Any]]:
        """Poll a single feed, parse items, and validate via RegionalAffinityClassifier."""
        url = feed['url']
        region = feed['region']
        ticker = feed.get('ticker', 'UNKNOWN')
        
        logger.info(f"Polling feed for [{region}] {ticker}: {url}")
        content = await self.client.fetch_feed(url)
        
        if content:
            parsed_items = self.client.parse_feed(content, region)
            verified_items = []

            for item in parsed_items:
                validation = self.classifier.classify_and_validate(
                    headline=item.get("title", ""),
                    summary=item.get("description", ""),
                    expected_region=region,
                    expected_ticker=ticker,
                    allow_reroute=False
                )
                if validation:
                    item['market_region'] = validation['market_region']
                    item['index_ticker'] = validation['index_ticker']
                    verified_items.append(item)

            logger.info(f"Retrieved {len(parsed_items)} raw items -> {len(verified_items)} verified for [{region}] {ticker}")
            return verified_items
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
