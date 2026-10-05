import re
import html
import hashlib
import logging
from typing import Optional, Set, List, Dict, Any

logger = logging.getLogger(__name__)

# Common financial publishers attached to RSS headlines
KNOWN_PUBLISHERS = [
    "Reuters", "reuters.com", "Bloomberg", "CNBC", "Financial Times", "FT",
    "Wall Street Journal", "WSJ", "The Wall Street Journal", "MarketWatch",
    "Barron's", "Fox Business", "Yahoo Finance", "The Economic Times",
    "Economic Times", "Moneycontrol", "Mint", "Business Standard", "NDTV Profit",
    "Livemint", "BBC", "CNN", "Forbes", "Investing.com", "Seeking Alpha"
]

def clean_headline_text(raw_text: str) -> str:
    """
    Strips HTML markup, publisher suffixes, and extra whitespace
    to extract the core financial headline.
    """
    if not raw_text:
        return ""
    
    # 1. Unescape HTML and remove tags
    unescaped = html.unescape(str(raw_text))
    clean = re.sub(r'<[^>]+>', ' ', unescaped)
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    # 2. Strip publisher suffix (e.g. "Headline text - Reuters" or "Headline | Bloomberg")
    for sep in [" - ", " | ", " — "]:
        if sep in clean:
            parts = [p.strip() for p in clean.split(sep) if p.strip()]
            if len(parts) > 1:
                # If the trailing segment is a known publisher or short source name (<= 30 chars)
                last_part = parts[-1]
                if any(pub.lower() == last_part.lower() for pub in KNOWN_PUBLISHERS) or len(last_part) <= 25:
                    clean = sep.join(parts[:-1]).strip()
    
    return clean

def canonical_fingerprint(raw_text: str) -> str:
    """
    Produces a normalized, deterministic string fingerprint for deduplication.
    Lowercases and keeps only alphanumeric characters.
    """
    clean = clean_headline_text(raw_text).lower()
    # Retain only letters and numbers
    alpha_num = re.sub(r'[^a-z0-9]', '', clean)
    if not alpha_num:
        return ""
    return hashlib.sha256(alpha_num.encode('utf-8')).hexdigest()

class NewsDeduplicator:
    """
    Thread-safe and async-compatible deduplication tracker
    for both intra-run batch filtering and cross-run database caching.
    """
    def __init__(self, existing_fingerprints: Optional[Set[str]] = None):
        self.seen_fingerprints: Set[str] = set(existing_fingerprints or [])

    def is_duplicate(self, text: str) -> bool:
        """Returns True if the headline has already been seen; otherwise marks it seen and returns False."""
        fp = canonical_fingerprint(text)
        if not fp:
            return True # Treat empty strings as duplicates
        if fp in self.seen_fingerprints:
            return True
        self.seen_fingerprints.add(fp)
        return False

    def filter_batch(self, items: List[Dict[str, Any]], text_key: str = "title") -> List[Dict[str, Any]]:
        """Filters a list of news items, dropping redundant records."""
        unique_items = []
        duplicate_count = 0
        for item in items:
            raw_text = item.get(text_key, "")
            if isinstance(raw_text, dict):
                # Handle nested dict like item['data']['headline']
                raw_text = raw_text.get("headline", "")
            if not self.is_duplicate(str(raw_text)):
                unique_items.append(item)
            else:
                duplicate_count += 1

        if duplicate_count > 0:
            logger.info(f"Deduplicator dropped {duplicate_count} duplicate news items from batch.")
        return unique_items
