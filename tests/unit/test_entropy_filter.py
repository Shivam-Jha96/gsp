"""
Unit tests for Normalized Shannon Entropy Filtering in Valence Signal Engine.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from signal_engine.ema import calculate_shannon_entropy, resolve_directional_stance


class TestEntropyFilter(unittest.TestCase):
    def test_absolute_certainty_zero_entropy(self):
        # 100% Bullish -> 0.0 entropy
        h_bull = calculate_shannon_entropy(p_bull=1.0, p_bear=0.0)
        self.assertAlmostEqual(h_bull, 0.0, places=4)
        
        # 100% Bearish -> 0.0 entropy
        h_bear = calculate_shannon_entropy(p_bull=0.0, p_bear=1.0)
        self.assertAlmostEqual(h_bear, 0.0, places=4)

    def test_maximum_ambiguity_unit_entropy(self):
        # 50/50 split -> 1.0 entropy (maximum epistemic conflict)
        h_split = calculate_shannon_entropy(p_bull=0.5, p_bear=0.5)
        self.assertAlmostEqual(h_split, 1.0, places=4)

    def test_entropy_symmetry(self):
        # H(0.7, 0.3) == H(0.3, 0.7)
        h_1 = calculate_shannon_entropy(0.7, 0.3)
        h_2 = calculate_shannon_entropy(0.3, 0.7)
        self.assertAlmostEqual(h_1, h_2, places=5)
        self.assertGreater(h_1, 0.0)
        self.assertLess(h_1, 1.0)

    def test_unnormalized_probabilities(self):
        # Probabilities summing to something other than 1.0 (e.g. 0.08 and 0.02)
        h = calculate_shannon_entropy(0.08, 0.02)
        # 0.8 / 0.2 split
        h_expected = calculate_shannon_entropy(0.8, 0.2)
        self.assertAlmostEqual(h, h_expected, places=5)

    def test_numerical_stability_edge_cases(self):
        # Zero probabilities
        h_zero = calculate_shannon_entropy(0.0, 0.0)
        self.assertEqual(h_zero, 1.0)
        
        # Extremely small probabilities
        h_tiny = calculate_shannon_entropy(1e-12, 1e-12)
        self.assertAlmostEqual(h_tiny, 1.0, places=3)

    def test_resolve_directional_stance_with_entropy(self):
        # Low entropy + strong EMA -> Directional
        stance_bull = resolve_directional_stance(ema_val=12.0, entropy=0.40, threshold=5.0)
        self.assertEqual(stance_bull, "BULLISH")
        
        stance_bear = resolve_directional_stance(ema_val=-10.0, entropy=0.50, threshold=5.0)
        self.assertEqual(stance_bear, "BEARISH")
        
        # High entropy (>0.96) -> Forced NEUTRAL even if EMA is large
        stance_conflicted = resolve_directional_stance(ema_val=15.0, entropy=0.98, threshold=5.0)
        self.assertEqual(stance_conflicted, "NEUTRAL")
        
        # Inside deadband -> NEUTRAL regardless of entropy
        stance_deadband = resolve_directional_stance(ema_val=3.0, entropy=0.10, threshold=5.0)
        self.assertEqual(stance_deadband, "NEUTRAL")


if __name__ == "__main__":
    unittest.main()
