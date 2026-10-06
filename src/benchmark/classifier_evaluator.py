"""
Ingestion & Regional Affinity Classifier Benchmarking for Valence.

Evaluates:
- Cross-Region Contamination Rate across IN, US, UK, JP
- Noise Rejection Ratio (Financial vs Non-Financial articles)
- NewsDeduplicator yield and canonical fingerprint consistency
"""

import sys
import os
import logging
from typing import Dict, Any, List

# Ensure src is on sys.path
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from ingestion.classifier import RegionalAffinityClassifier
from ingestion.dedup import NewsDeduplicator, canonical_fingerprint

logger = logging.getLogger(__name__)


BENCHMARK_REGIONAL_SUITE = [
    # US Targeted
    {"text": "S&P 500 and Nasdaq rally as Fed signals terminal rate cut cycle.", "intended": "US"},
    {"text": "Apple and Microsoft announce major capital expenditure in US data centers.", "intended": "US"},
    {"text": "Wall Street futures climb ahead of non-farm payrolls data release.", "intended": "US"},
    
    # India Targeted
    {"text": "Nifty 50 and Sensex touch record highs led by Reliance and HDFC Bank.", "intended": "IN"},
    {"text": "Reserve Bank of India Governor comments on domestic banking liquidity.", "intended": "IN"},
    {"text": "Dalal Street celebrates strong quarterly revenue print from TCS.", "intended": "IN"},
    
    # UK Targeted
    {"text": "FTSE 100 closes higher as Bank of England cuts policy rates by 25 bps.", "intended": "UK"},
    {"text": "London Stock Exchange welcomes Shell and BP dividend expansion.", "intended": "UK"},
    {"text": "UK gilt yields stabilize following Treasury chancellor fiscal address.", "intended": "UK"},
    
    # Japan Targeted
    {"text": "Nikkei 225 surges past 38,000 as Tokyo Electron and Toyota gain.", "intended": "JP"},
    {"text": "Bank of Japan discusses future yield curve control parameters in Tokyo.", "intended": "JP"},
    {"text": "Topix index advances amidst record Japanese corporate buyback authorizations.", "intended": "JP"}
]

BENCHMARK_NOISE_SUITE = [
    # Non-financial noise
    {"text": "Local sports team clinches championship title in thrilling overtime victory.", "is_financial": False},
    {"text": "Celebrity couple spotted at annual summer music festival red carpet.", "is_financial": False},
    {"text": "Top ten weekend recipes for healthy summer barbecue gatherings.", "is_financial": False},
    {"text": "Astronomers discover new exoplanet with telescope in distant star cluster.", "is_financial": False},
    
    # Legitimate financial news
    {"text": "Treasury yield curve steepens as investors position for Fed monetary pivot.", "is_financial": True},
    {"text": "Crude oil futures slide 2% as inventory build surprises global commodities traders.", "is_financial": True},
    {"text": "Global equity markets rebound as central bank balance sheet expansion resumes.", "is_financial": True}
]


class ClassifierEvaluator:
    """
    Evaluates the regional affinity classifier and deduplication engines.
    """
    def __init__(self):
        self.classifier = RegionalAffinityClassifier()
        self.dedup = NewsDeduplicator()

    def evaluate_regional_affinity(self) -> Dict[str, Any]:
        """
        Tests cross-region contamination and classification accuracy.
        """
        total = len(BENCHMARK_REGIONAL_SUITE)
        correct_region = 0
        contamination_count = 0
        
        region_matrix: Dict[str, Dict[str, int]] = {
            "US": {"US": 0, "IN": 0, "UK": 0, "JP": 0, "OTHER": 0},
            "IN": {"US": 0, "IN": 0, "UK": 0, "JP": 0, "OTHER": 0},
            "UK": {"US": 0, "IN": 0, "UK": 0, "JP": 0, "OTHER": 0},
            "JP": {"US": 0, "IN": 0, "UK": 0, "JP": 0, "OTHER": 0},
        }

        for item in BENCHMARK_REGIONAL_SUITE:
            text = item["text"]
            intended = item["intended"]

            all_affinities = self.classifier.compute_affinities(text)
            primary_region = max(all_affinities, key=all_affinities.get) if all_affinities else "NONE"

            # Check if primary region matches intended
            if primary_region == intended:
                correct_region += 1
                region_matrix[intended][intended] += 1
            else:
                dest = primary_region if primary_region in region_matrix[intended] else "OTHER"
                region_matrix[intended][dest] += 1

            # Contamination check: Did any other non-intended region receive > 0 affinity?
            for reg, score in all_affinities.items():
                if reg != intended and score > 0.0:
                    contamination_count += 1
                    break

        accuracy = float(correct_region / total)
        contamination_rate = float(contamination_count / total)

        return {
            "total_samples": total,
            "regional_accuracy_pct": round(accuracy * 100.0, 2),
            "cross_region_contamination_pct": round(contamination_rate * 100.0, 2),
            "region_confusion_matrix": region_matrix
        }

    def evaluate_noise_rejection(self) -> Dict[str, Any]:
        """
        Measures noise rejection ratio: how accurately non-financial text is filtered.
        """
        total_noise = sum(1 for item in BENCHMARK_NOISE_SUITE if not item["is_financial"])
        total_financial = sum(1 for item in BENCHMARK_NOISE_SUITE if item["is_financial"])

        rejected_noise = 0
        accepted_financial = 0

        for item in BENCHMARK_NOISE_SUITE:
            text = item["text"]
            is_fin = item["is_financial"]

            affinities = self.classifier.compute_affinities(text)
            total_affinity_score = sum(affinities.values())
            has_affinity = (total_affinity_score > 0.0)

            if not is_fin:
                if not has_affinity and total_affinity_score == 0.0:
                    rejected_noise += 1
            else:
                # Legitimate financial news should either have affinity or market action pattern match
                if has_affinity or total_affinity_score > 0.0 or self.classifier._compiled_market_action_pattern.search(text):
                    accepted_financial += 1


        noise_rejection_rate = float(rejected_noise / max(1, total_noise))
        financial_retention_rate = float(accepted_financial / max(1, total_financial))

        return {
            "noise_rejection_pct": round(noise_rejection_rate * 100.0, 2),
            "financial_retention_pct": round(financial_retention_rate * 100.0, 2),
            "total_tested": len(BENCHMARK_NOISE_SUITE)
        }

    def evaluate_deduplication(self) -> Dict[str, Any]:
        """
        Tests canonical fingerprinting and deduplication yields.
        """
        base_headline = "US inflation hits 3-year low as energy costs decline"
        variations = [
            base_headline,
            f"{base_headline} - Reuters",
            f"{base_headline} - Bloomberg News",
            f"{base_headline} | CNBC",
            f"   {base_headline}   ",
            f"{base_headline} - reuters.com"
        ]

        fps = [canonical_fingerprint(v) for v in variations]
        all_match = all(fp == fps[0] for fp in fps)

        # Batch filter test
        items = [{"title": v, "id": i} for i, v in enumerate(variations)]
        deduper = NewsDeduplicator()
        filtered = deduper.filter_batch(items, text_key="title")

        return {
            "canonical_fingerprint_invariance": all_match,
            "input_syndications": len(variations),
            "retained_unique": len(filtered),
            "deduplication_yield_pct": round((1.0 - (len(filtered) / len(variations))) * 100.0, 2)
        }
