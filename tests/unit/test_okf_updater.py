import unittest
from unittest.mock import MagicMock
from src.knowledge_engine.okf_updater import get_available_models, DEFAULT_MODEL_FALLBACKS

class TestOKFUpdater(unittest.TestCase):
    def test_get_available_models_success(self):
        mock_client = MagicMock()
        mock_model_1 = MagicMock()
        mock_model_1.name = "models/gemini-3.8-flash"
        mock_model_1.supported_actions = ["generateContent"]

        mock_model_2 = MagicMock()
        mock_model_2.name = "models/gemini-3.7-flash"
        mock_model_2.supported_actions = ["generateContent"]

        mock_model_embed = MagicMock()
        mock_model_embed.name = "models/text-embedding-004"
        mock_model_embed.supported_actions = ["embedContent"]

        mock_client.models.list.return_value = [mock_model_1, mock_model_2, mock_model_embed]

        models = get_available_models(mock_client)
        self.assertIn("gemini-3.8-flash", models)
        self.assertIn("gemini-3.7-flash", models)
        self.assertNotIn("text-embedding-004", models)
        self.assertEqual(models[0], "gemini-3.8-flash")

    def test_get_available_models_api_error_fallback(self):
        mock_client = MagicMock()
        mock_client.models.list.side_effect = Exception("API rate limited")

        models = get_available_models(mock_client)
        self.assertEqual(models, DEFAULT_MODEL_FALLBACKS)

if __name__ == "__main__":
    unittest.main()
