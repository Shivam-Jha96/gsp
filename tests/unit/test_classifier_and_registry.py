import os
import sys
import unittest

# Ensure src/ is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from config.market_registry import (
    load_market_registry,
    get_all_region_codes,
    get_region_meta,
    build_rss_feeds
)
from ingestion.classifier import RegionalAffinityClassifier

class TestMarketRegistryAndClassifier(unittest.TestCase):

    def test_market_registry_structure(self):
        registry = load_market_registry()
        self.assertIsInstance(registry, dict)
        
        # Must have the 4 core regions
        for reg in ["IN", "US", "UK", "JP"]:
            self.assertIn(reg, registry)
            meta = registry[reg]
            self.assertIn("name", meta)
            self.assertIn("currency", meta)
            self.assertIn("locale", meta)
            self.assertIn("hl", meta["locale"])
            self.assertIn("gl", meta["locale"])
            self.assertIn("ceid", meta["locale"])
            self.assertIn("indices", meta)
            self.assertGreaterEqual(len(meta["indices"]), 3)
            self.assertIn("anchors", meta)
            self.assertGreaterEqual(len(meta["anchors"]), 5)
            self.assertIn("okf_file", meta)
            self.assertTrue(os.path.exists(os.path.join(os.path.dirname(__file__), "../../", meta["okf_file"])))

    def test_build_rss_feeds(self):
        feeds = build_rss_feeds()
        self.assertGreater(len(feeds), 0)
        # Every index generates 2 feeds (Google General + Reuters Institutional)
        for feed in feeds:
            self.assertIn("url", feed)
            self.assertIn("region", feed)
            self.assertIn("ticker", feed)
            self.assertIn(feed["region"], ["IN", "US", "UK", "JP"])
            # Must include geotargeting params
            self.assertIn("&gl=", feed["url"])
            self.assertIn("&hl=", feed["url"])
            self.assertIn("&ceid=", feed["url"])

    def test_classifier_valid_regional_acceptance(self):
        classifier = RegionalAffinityClassifier()

        # 1. Indian headline under IN
        res_in = classifier.classify_and_validate(
            headline="Sensex, Nifty end lower again; FMCG and auto stocks drag Dalal Street",
            summary="Foreign investors continued selling as RBI monetary policy outlook stayed cautious.",
            expected_region="IN",
            expected_ticker="Nifty 50"
        )
        self.assertIsNotNone(res_in)
        self.assertEqual(res_in["market_region"], "IN")
        self.assertEqual(res_in["index_ticker"], "Nifty 50")

        # 2. US headline under US
        res_us = classifier.classify_and_validate(
            headline="S&P 500 and Nasdaq rally as tech leaders gain ahead of Fed meeting",
            summary="Treasury yields dropped slightly after moderate jobs data print on Wall Street.",
            expected_region="US",
            expected_ticker="S&P 500"
        )
        self.assertIsNotNone(res_us)
        self.assertEqual(res_us["market_region"], "US")
        self.assertEqual(res_us["index_ticker"], "S&P 500")

        # 3. UK headline under UK
        res_uk = classifier.classify_and_validate(
            headline="FTSE 100 drops to three-month low as surging bond yields hit London banks",
            summary="Bank of England policy makers warned sticky inflation could prolong high interest rates.",
            expected_region="UK",
            expected_ticker="FTSE 100"
        )
        self.assertIsNotNone(res_uk)
        self.assertEqual(res_uk["market_region"], "UK")
        self.assertEqual(res_uk["index_ticker"], "FTSE 100")

        # 4. Japan headline under JP
        res_jp = classifier.classify_and_validate(
            headline="Nikkei 225 rebounds 2% as yen stabilizes following Bank of Japan comments",
            summary="Tokyo shares bounced after governor Kazuo Ueda reiterated gradual policy normalization.",
            expected_region="JP",
            expected_ticker="Nikkei 225"
        )
        self.assertIsNotNone(res_jp)
        self.assertEqual(res_jp["market_region"], "JP")
        self.assertEqual(res_jp["index_ticker"], "Nikkei 225")

    def test_classifier_cross_region_rejection(self):
        classifier = RegionalAffinityClassifier()

        # Case 1: Indian shares pulled under UK FTSE query (The actual Reuters bug observed)
        res_uk_contaminant = classifier.classify_and_validate(
            headline="Indian benchmark shares post longest weekly losing run in 25 years - Reuters",
            summary="Mumbai stock indices tumble amid foreign capital outflows.",
            expected_region="UK",
            expected_ticker="FTSE 100"
        )
        self.assertIsNone(res_uk_contaminant, "Should reject Indian shares under UK")

        # Case 2: Pure US Wall Street news pulled under India Nifty query (The user's reported bug)
        res_in_contaminant = classifier.classify_and_validate(
            headline="Wall Street slides as tech selloff deepens ahead of Fed meeting - Bloomberg",
            summary="The Dow and Nasdaq experienced heavy volume as Treasury yields climbed.",
            expected_region="IN",
            expected_ticker="Nifty 50"
        )
        self.assertIsNone(res_in_contaminant, "Should reject US Wall Street news under India")

        # Case 3: Completely unrelated non-financial noise (e.g. crime or celebrity)
        res_noise = classifier.classify_and_validate(
            headline="Tennessee inmate survives execution attempt following legal challenge - Reuters",
            summary="The court issued a temporary stay of execution for the convicted offender.",
            expected_region="JP",
            expected_ticker="JP Mothers"
        )
        self.assertIsNone(res_noise, "Should reject non-financial news with 0 market affinity")

if __name__ == "__main__":
    unittest.main()
