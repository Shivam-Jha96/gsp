import aiohttp
import logging
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSSClient:
    def __init__(self, timeout: int = 10):
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def fetch_feed(self, url: str) -> Optional[str]:
        """Fetch RSS feed content asynchronously."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def parse_feed(self, content: str, market_region: str) -> List[Dict[str, Any]]:
        """Parse RSS feed XML content and tag with market region."""
        items = []
        try:
            # Using basic ElementTree for MVP to avoid extra dependencies like feedparser
            root = ET.fromstring(content)
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                desc_elem = item.find('description')
                
                title = title_elem.text if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                description = desc_elem.text if desc_elem is not None else ""

                if title or description:
                    items.append({
                        "title": title.strip(),
                        "link": link.strip(),
                        "published_at": pub_date.strip(),
                        "description": description.strip(),
                        "market_region": market_region,
                    })
        except Exception as e:
            logger.error(f"Error parsing feed content: {e}")
            
        # Limit to the top 3 headlines per region to stay under the 15 RPM free tier limit
        return items[:3]
