import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_REGISTRY_CACHE: Optional[Dict[str, Any]] = None

def get_registry_path() -> str:
    """Returns absolute path to market_registry.json."""
    return os.path.join(os.path.dirname(__file__), "market_registry.json")

def load_market_registry(force_reload: bool = False) -> Dict[str, Any]:
    """Loads and caches the market registry configuration."""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is not None and not force_reload:
        return _REGISTRY_CACHE

    reg_path = get_registry_path()
    if not os.path.exists(reg_path):
        raise FileNotFoundError(f"Market registry configuration not found at: {reg_path}")

    with open(reg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _REGISTRY_CACHE = data
    return _REGISTRY_CACHE

def get_all_region_codes() -> List[str]:
    """Returns list of all active region codes (e.g. ['IN', 'US', 'UK', 'JP'])."""
    return list(load_market_registry().keys())

def get_region_meta(region_code: str) -> Optional[Dict[str, Any]]:
    """Returns metadata for a specific region code."""
    return load_market_registry().get(region_code)

def build_rss_feeds() -> List[Dict[str, Any]]:
    """
    Dynamically generates geotargeted Google News & Reuters RSS feed descriptors
    from the declarative market registry.
    """
    registry = load_market_registry()
    feeds = []

    for region_code, region_meta in registry.items():
        locale = region_meta.get("locale", {})
        hl = locale.get("hl", "en-US")
        gl = locale.get("gl", "US")
        ceid = locale.get("ceid", "US:en")

        locale_params = f"&hl={hl}&gl={gl}&ceid={ceid}"

        for index_meta in region_meta.get("indices", []):
            ticker = index_meta["ticker"]
            search_term = index_meta["search_term"]

            # 1. Geotargeted General Market News
            feeds.append({
                "url": f"https://news.google.com/rss/search?q={search_term}{locale_params}",
                "region": region_code,
                "ticker": ticker
            })

            # 2. Geotargeted Reuters Institutional Channel
            feeds.append({
                "url": f"https://news.google.com/rss/search?q={search_term}+site:reuters.com{locale_params}",
                "region": region_code,
                "ticker": ticker
            })

    return feeds
