import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from config.market_registry import load_market_registry

logger = logging.getLogger(__name__)

class RegionalAffinityClassifier:
    """
    Evaluates news headlines and descriptions against the declarative market registry
    to compute regional affinity scores, filter irrelevant noise, and eliminate
    cross-region contamination.
    """
    def __init__(self, registry: Optional[Dict[str, Any]] = None):
        self.registry = registry or load_market_registry()
        self._compiled_ticker_patterns: Dict[str, List[Tuple[re.Pattern, str]]] = {}
        self._compiled_anchor_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compiles regex boundary patterns for high-performance $O(1)$ matching."""
        for region_code, region_meta in self.registry.items():
            # 1. Compile index ticker and alias patterns (Weight = 3.0)
            ticker_patterns = []
            for idx in region_meta.get("indices", []):
                ticker_name = idx["ticker"]
                aliases = idx.get("aliases", []) + [ticker_name.lower()]
                # Escape and sort by length descending to match longest phrases first
                aliases_sorted = sorted(set(aliases), key=len, reverse=True)
                escaped_aliases = [re.escape(a) for a in aliases_sorted if a.strip()]
                if escaped_aliases:
                    pattern = re.compile(r'\b(?:' + '|'.join(escaped_aliases) + r')\b', re.IGNORECASE)
                    ticker_patterns.append((pattern, ticker_name))
            self._compiled_ticker_patterns[region_code] = ticker_patterns

            # 2. Compile regional economic anchor patterns (Weight = 1.0)
            anchors = region_meta.get("anchors", [])
            anchors_sorted = sorted(set(anchors), key=len, reverse=True)
            escaped_anchors = [re.escape(a) for a in anchors_sorted if a.strip()]
            if escaped_anchors:
                self._compiled_anchor_patterns[region_code] = re.compile(
                    r'\b(?:' + '|'.join(escaped_anchors) + r')\b', re.IGNORECASE
                )

    def compute_affinities(self, text: str) -> Dict[str, float]:
        """
        Computes regional affinity scores across all registered markets.
        Affinity = 3.0 * TickerMatches + 1.0 * AnchorMatches
        """
        scores: Dict[str, float] = {}

        for region_code in self.registry.keys():
            score = 0.0

            # Check index ticker matches
            for pattern, _ in self._compiled_ticker_patterns.get(region_code, []):
                if pattern.search(text):
                    score += 3.0
                    break

            # Check economic anchor matches
            anchor_pattern = self._compiled_anchor_patterns.get(region_code)
            if anchor_pattern and anchor_pattern.search(text):
                score += 1.0

            if score > 0.0:
                scores[region_code] = score

        return scores

    def classify_and_validate(
        self,
        headline: str,
        summary: str,
        expected_region: str,
        expected_ticker: str,
        allow_reroute: bool = False
    ) -> Optional[Dict[str, str]]:
        """
        Validates whether an ingested item belongs to the expected region.
        - If valid: returns dict with verified 'market_region' and 'index_ticker'.
        - If cross-region contaminant or non-market noise: returns None (or re-routes).
        """
        content = f"{headline} {summary}".strip()
        if not content:
            return None

        affinities = self.compute_affinities(content)

        # 1. Expected Region Validated
        if affinities.get(expected_region, 0.0) > 0.0:
            return {
                "market_region": expected_region,
                "index_ticker": expected_ticker
            }

        # 2. Cross-Region Contaminant Detected
        if affinities:
            dominant_region, dom_score = max(affinities.items(), key=lambda item: item[1])

            if allow_reroute and dom_score >= 3.0:
                # Find matching ticker in dominant region if present
                detected_ticker = "BROAD_MARKET"
                for pattern, t_name in self._compiled_ticker_patterns.get(dominant_region, []):
                    if pattern.search(content):
                        detected_ticker = t_name
                        break

                logger.info(
                    f"[CLASSIFIER: RE-ROUTE] '{headline[:50]}...' pulled under [{expected_region}] "
                    f"-> re-routed to [{dominant_region}] {detected_ticker} (Affinity: {dom_score})"
                )
                return {
                    "market_region": dominant_region,
                    "index_ticker": detected_ticker
                }

            logger.warning(
                f"[CLASSIFIER: REJECT-CONTAMINANT] '{headline[:50]}...' pulled under [{expected_region}] "
                f"rejected because dominant affinity is [{dominant_region}] (Score: {dom_score})"
            )
            return None

        # 3. Non-Financial or General Noise Detected
        logger.warning(
            f"[CLASSIFIER: REJECT-NOISE] '{headline[:50]}...' rejected (0 affinity across all regions)"
        )
        return None
