import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_REGISTRY_CACHE: Optional[Dict[str, Any]] = None
_ASSET_CLASSES_CACHE: Optional[Dict[str, Any]] = None
_CONSTITUENTS_CACHE: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

def get_registry_path() -> str:
    """Returns absolute path to market_registry.json."""
    return os.path.join(os.path.dirname(__file__), "market_registry.json")

def get_asset_classes_path() -> str:
    """Returns absolute path to asset_classes.json."""
    return os.path.join(os.path.dirname(__file__), "asset_classes.json")

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

def load_asset_classes(force_reload: bool = False) -> Dict[str, Any]:
    """Loads and caches the asset classes configuration."""
    global _ASSET_CLASSES_CACHE
    if _ASSET_CLASSES_CACHE is not None and not force_reload:
        return _ASSET_CLASSES_CACHE

    ac_path = get_asset_classes_path()
    if not os.path.exists(ac_path):
        logger.warning(f"Asset classes configuration not found at: {ac_path}. Using empty.")
        return {}

    with open(ac_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    _ASSET_CLASSES_CACHE = data
    return _ASSET_CLASSES_CACHE

def get_all_region_codes() -> List[str]:
    """Returns list of all active region codes (e.g. ['IN', 'US', 'UK', 'JP'])."""
    return list(load_market_registry().keys())

def get_region_meta(region_code: str) -> Optional[Dict[str, Any]]:
    """Returns metadata for a specific region code."""
    return load_market_registry().get(region_code)

def load_region_constituents(region_code: str, force_reload: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """
    Loads constituent companies for a given region from its declarative OKF constituents file.
    Returns mapping: {index_ticker: [ {symbol, name, aliases}, ... ]}
    """
    global _CONSTITUENTS_CACHE
    if not force_reload and region_code in _CONSTITUENTS_CACHE:
        return _CONSTITUENTS_CACHE[region_code]

    meta = get_region_meta(region_code)
    if not meta or not meta.get("constituents_file"):
        return {}

    rel_path = meta["constituents_file"]
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_path = os.path.join(repo_root, rel_path)
    if not os.path.exists(abs_path):
        logger.warning(f"Constituents file not found at: {abs_path}")
        return {}

    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        indices_map = data.get("indices", {})
        _CONSTITUENTS_CACHE[region_code] = indices_map
        return indices_map
    except Exception as e:
        logger.error(f"Error loading constituents file {abs_path}: {e}")
        return {}

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
            asset_class = index_meta.get("asset_class", "equity")

            # 1. Geotargeted General Market News
            feeds.append({
                "url": f"https://news.google.com/rss/search?q={search_term}{locale_params}",
                "region": region_code,
                "ticker": ticker,
                "asset_class": asset_class
            })

            # 2. Geotargeted Reuters Institutional Channel
            feeds.append({
                "url": f"https://news.google.com/rss/search?q={search_term}+site:reuters.com{locale_params}",
                "region": region_code,
                "ticker": ticker,
                "asset_class": asset_class
            })

    return feeds
