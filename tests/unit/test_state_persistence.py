import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.ui.state_persistence import (
    TIMEFRAME_MAP, TIMEFRAME_TO_QP,
    REGION_MAP, REGION_TO_QP,
    TZ_MAP, TZ_TO_QP,
    EMA_MAP, EMA_TO_QP,
    FEED_MAP, FEED_TO_QP,
    init_session_persistence,
    sync_preference_to_query_params,
    sync_all_preferences_to_query_params,
    get_persisted_feed_index,
    render_local_storage_sync_script,
    _get_query_param,
    _set_query_param
)


class TestStatePersistence(unittest.TestCase):
    def test_bidirectional_timeframe_mappings(self):
        for full_label, qp in TIMEFRAME_TO_QP.items():
            self.assertEqual(TIMEFRAME_MAP[qp], full_label)

    def test_bidirectional_region_mappings(self):
        for full_label, qp in REGION_TO_QP.items():
            self.assertEqual(REGION_MAP[qp], full_label)

    def test_bidirectional_tz_mappings(self):
        for full_label, qp in TZ_TO_QP.items():
            self.assertEqual(TZ_MAP[qp], full_label)

    def test_bidirectional_ema_mappings(self):
        for full_label, qp in EMA_TO_QP.items():
            self.assertEqual(EMA_MAP[qp], full_label)

    def test_bidirectional_feed_mappings(self):
        for full_label, qp in FEED_TO_QP.items():
            self.assertEqual(FEED_MAP[qp], full_label)

    def test_get_persisted_feed_index(self):
        options = ["All 120", "Bullish 45", "Bearish 35", "Neutral 40"]
        
        with patch('streamlit.session_state', {"feed_sentiment_category": "Bullish"}):
            self.assertEqual(get_persisted_feed_index(options), 1)

        with patch('streamlit.session_state', {"feed_sentiment_category": "Bearish"}):
            self.assertEqual(get_persisted_feed_index(options), 2)

        with patch('streamlit.session_state', {"feed_sentiment_category": "Neutral"}):
            self.assertEqual(get_persisted_feed_index(options), 3)

        with patch('streamlit.session_state', {"feed_sentiment_category": "All"}):
            self.assertEqual(get_persisted_feed_index(options), 0)

    def test_init_session_persistence_defaults(self):
        mock_session = {}
        mock_qp = {}
        with patch('streamlit.session_state', mock_session), \
             patch('streamlit.query_params', mock_qp):
            init_session_persistence()

            self.assertEqual(mock_session["filter_timeframe"], "7 Days")
            self.assertEqual(mock_session["filter_region"], "India (IN)")
            self.assertEqual(mock_session["filter_timezone"], "Asia/Kolkata (IST)")
            self.assertEqual(mock_session["filter_ema_window"], "4 Periods")
            self.assertEqual(mock_session["filter_chart_display"], "All Indices")
            self.assertEqual(mock_session["feed_sentiment_category"], "All")

            # Check that query params were mirrored
            self.assertEqual(mock_qp["tf"], "7D")
            self.assertEqual(mock_qp["region"], "IN")
            self.assertEqual(mock_qp["tz"], "IST")
            self.assertEqual(mock_qp["ema"], "4")
            self.assertEqual(mock_qp["chart"], "All")
            self.assertEqual(mock_qp["feed"], "all")

    def test_init_session_persistence_from_query_params(self):
        mock_session = {}
        mock_qp = {
            "tf": "1D",
            "region": "US",
            "tz": "EST",
            "ema": "8",
            "feed": "bullish"
        }
        with patch('streamlit.session_state', mock_session), \
             patch('streamlit.query_params', mock_qp):
            init_session_persistence()

            self.assertEqual(mock_session["filter_timeframe"], "1 Day")
            self.assertEqual(mock_session["filter_region"], "United States (US)")
            self.assertEqual(mock_session["filter_timezone"], "America/New_York (EST)")
            self.assertEqual(mock_session["filter_ema_window"], "8 Periods")
            self.assertEqual(mock_session["feed_sentiment_category"], "Bullish")

    def test_cross_region_ticker_validation(self):
        df_signals = pd.DataFrame({
            "market_region": ["IN", "IN", "US", "US"],
            "index_ticker": ["NIFTY 50", "BANK NIFTY", "S&P 500", "NASDAQ 100"]
        })

        mock_session = {}
        # User provides US region with Indian ticker NIFTY 50
        mock_qp = {
            "region": "US",
            "chart": "NIFTY 50"
        }
        with patch('streamlit.session_state', mock_session), \
             patch('streamlit.query_params', mock_qp):
            init_session_persistence(df_signals)

            # NIFTY 50 should be rejected for US and reset to All Indices
            self.assertEqual(mock_session["filter_chart_display"], "All Indices")

        # Now test with valid US ticker
        mock_session_valid = {}
        mock_qp_valid = {
            "region": "US",
            "chart": "S&P 500"
        }
        with patch('streamlit.session_state', mock_session_valid), \
             patch('streamlit.query_params', mock_qp_valid):
            init_session_persistence(df_signals)

            self.assertEqual(mock_session_valid["filter_chart_display"], "S&P 500")

    def test_local_storage_sync_script_renders(self):
        with patch('streamlit.markdown') as mock_md:
            render_local_storage_sync_script()
            self.assertTrue(mock_md.called)
            call_args = mock_md.call_args[0][0]
            self.assertIn("valence_persisted_query", call_args)
            self.assertIn("localStorage.setItem", call_args)

    def test_sync_all_preferences_to_query_params(self):
        mock_session = {
            "filter_timeframe": "1 Day",
            "filter_region": "United States (US)",
            "filter_timezone": "America/New_York (EST)",
            "filter_ema_window": "8 Periods",
            "filter_chart_display": "S&P 500",
            "feed_sentiment_category": "Bullish"
        }
        mock_qp = {}
        with patch('streamlit.session_state', mock_session), \
             patch('streamlit.query_params', mock_qp):
            sync_all_preferences_to_query_params()
            self.assertEqual(mock_qp["tf"], "1D")
            self.assertEqual(mock_qp["region"], "US")
            self.assertEqual(mock_qp["tz"], "EST")
            self.assertEqual(mock_qp["ema"], "8")
            self.assertEqual(mock_qp["chart"], "S&P 500")
            self.assertEqual(mock_qp["feed"], "bullish")



if __name__ == '__main__':
    unittest.main()
