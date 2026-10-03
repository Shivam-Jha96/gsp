import unittest
from ingestion.dedup import NewsDeduplicator, canonical_fingerprint, clean_headline_text

class TestDeduplication(unittest.TestCase):
    def test_canonical_fingerprint(self):
        h1 = "India benchmark shares log worst month since March as oil, global rate hikes spark outflows - Reuters"
        h2 = "India benchmark shares log worst month since March as oil, global rate hikes spark outflows - reuters.com"
        h3 = "India benchmark shares log worst month since March as oil, global rate hikes spark outflows"
        
        fp1 = canonical_fingerprint(h1)
        fp2 = canonical_fingerprint(h2)
        fp3 = canonical_fingerprint(h3)
        
        self.assertEqual(fp1, fp2)
        self.assertEqual(fp2, fp3)
        self.assertTrue(len(fp1) > 20)

    def test_news_deduplicator(self):
        dedup = NewsDeduplicator()
        
        # First occurrence should not be a duplicate
        self.assertFalse(dedup.is_duplicate("Sensex rallies 500 points on strong earnings - Economic Times"))
        
        # Second occurrence with minor publisher variation should be caught as duplicate
        self.assertTrue(dedup.is_duplicate("Sensex rallies 500 points on strong earnings - ET"))
        self.assertTrue(dedup.is_duplicate("Sensex rallies 500 points on strong earnings"))

        # Genuinely different news should pass
        self.assertFalse(dedup.is_duplicate("Nifty Bank slides 200 points as private banks stumble"))

    def test_batch_filtering(self):
        items = [
            {"title": "Wall Street drops 1% ahead of jobs report - Bloomberg", "market_region": "US"},
            {"title": "Wall Street drops 1% ahead of jobs report", "market_region": "US"},
            {"title": "FTSE 100 flat as energy gains offset mining losses - Reuters", "market_region": "UK"},
        ]
        dedup = NewsDeduplicator()
        filtered = dedup.filter_batch(items, text_key="title")
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["market_region"], "US")
        self.assertEqual(filtered[1]["market_region"], "UK")

if __name__ == '__main__':
    unittest.main()
