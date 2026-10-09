import unittest
from unittest.mock import MagicMock, patch
from src.ai_engine.clm_client import CLMClient, Choice, ChoiceAnswer, SystemOneResponse


class TestCLMClient(unittest.TestCase):
    def setUp(self):
        self.client = CLMClient(
            base_url="https://mock-clm-server.modal.run",
            api_key="mock_key",
            model="clm-test",
            timeout=10.0
        )

    def test_choice_to_dict(self):
        c = Choice(instructions="Evaluate market bias", criteria={"Bullish": None, "Bearish": None})
        d = c.to_dict()
        self.assertEqual(d["type"], "choice")
        self.assertEqual(d["instructions"], "Evaluate market bias")
        self.assertIn("Bullish", d["criteria"])

    @patch("src.ai_engine.clm_client.requests.Session.post")
    def test_system_one_dict_answers(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "model": "clm-test",
            "answers": {
                "direction": {
                    "type": "choice",
                    "choice": "Bullish",
                    "confidence": 0.85,
                    "probabilities": {
                        "Bullish": 0.85,
                        "Bearish": 0.10,
                        "Neutral": 0.05
                    }
                }
            }
        }
        mock_post.return_value = mock_resp

        response = self.client.system_one(
            state="Tech rally pushes indices to new records",
            questions={
                "direction": Choice(instructions="Rate equity direction")
            }
        )

        self.assertIn("direction", response.choices)
        choice_ans = response.choices["direction"]
        self.assertEqual(choice_ans.choice, "Bullish")
        self.assertAlmostEqual(choice_ans.probabilities["Bullish"], 0.85)
        self.assertAlmostEqual(choice_ans.probabilities["Bearish"], 0.10)
        self.assertAlmostEqual(choice_ans.probabilities["Neutral"], 0.05)

        # Verify POST call details
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://mock-clm-server.modal.run/v1/systemone")
        self.assertIn("Authorization", kwargs["headers"])
        self.assertEqual(kwargs["json"]["model"], "clm-test")

    @patch("src.ai_engine.clm_client.requests.Session.post")
    def test_system_one_list_answers_fallback(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "answers": [
                {
                    "name": "direction",
                    "choice": "Bearish",
                    "probabilities": {"Bullish": 0.05, "Bearish": 0.90, "Neutral": 0.05}
                }
            ]
        }
        mock_post.return_value = mock_resp

        response = self.client.system_one(
            state="Central bank raises rates unexpectedly",
            questions={"direction": {"type": "choice"}}
        )

        choice_ans = response.choices["direction"]
        self.assertEqual(choice_ans.choice, "Bearish")
        self.assertAlmostEqual(choice_ans.probabilities["Bearish"], 0.90)


if __name__ == "__main__":
    unittest.main()
