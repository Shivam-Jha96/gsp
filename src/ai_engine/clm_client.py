"""
Native Sovereign HTTP Client for Valence Contrastive Language Model (CLM-8B).
Directly interfaces with the self-hosted Modal ASGI endpoint running vLLM Qwen3-8B
and contrastive-lm with zero third-party SDK dependencies.
"""

import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DEFAULT_MODAL_CLM_URL = "https://shivam-jha96--clm-macro-engine-clm-server.modal.run"


class Choice:
    """Represents a bipolar contrastive question specification."""
    def __init__(self, instructions: str, criteria: Optional[Dict[str, Any]] = None):
        self.instructions = instructions
        self.criteria = criteria or {"Bullish": None, "Bearish": None, "Neutral": None}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "choice",
            "instructions": self.instructions,
            "criteria": self.criteria
        }


class ChoiceAnswer:
    """Represents the normalized probability distribution answer from CLM."""
    def __init__(self, choice: str = "Neutral", probabilities: Optional[Dict[str, float]] = None):
        self.choice = choice
        self.probabilities = probabilities or {"Bullish": 0.0, "Bearish": 0.0, "Neutral": 1.0}


class SystemOneResponse:
    """Encapsulates the response from the self-hosted /v1/systemone endpoint."""
    def __init__(self, choices: Dict[str, ChoiceAnswer], raw: Optional[Dict[str, Any]] = None):
        self.choices = choices
        self.raw = raw or {}


class CLMClient:
    """
    Direct, sovereign HTTP client communicating with Valence's self-hosted
    Modal GPU serverless endpoint (vLLM Qwen3-8B + contrastive-lm).
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "clm-latest",
        timeout: float = 120.0
    ):
        self.base_url = (base_url or os.environ.get("CLM_SERVER_URL") or DEFAULT_MODAL_CLM_URL).rstrip("/")
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY") or os.environ.get("CLM_API_KEY") or "sovereign_local_key"
        self.model = model
        self.timeout = timeout
        self.session = requests.Session()

    def system_one(
        self,
        state: str,
        questions: Dict[str, Any]
    ) -> SystemOneResponse:
        """
        Sends state text and contrastive choices to the self-hosted endpoint.
        Returns a SystemOneResponse containing choice probabilities on the 2-simplex.
        """
        formatted_questions = {}
        for q_name, q_val in questions.items():
            if isinstance(q_val, Choice):
                formatted_questions[q_name] = q_val.to_dict()
            elif isinstance(q_val, dict):
                formatted_questions[q_name] = q_val
            else:
                formatted_questions[q_name] = {
                    "type": "choice",
                    "instructions": str(q_val),
                    "criteria": {"Bullish": None, "Bearish": None, "Neutral": None}
                }

        payload = {
            "state": state,
            "model": self.model,
            "questions": formatted_questions
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Valence-CLM-Native-Client/1.0"
        }

        url = f"{self.base_url}/v1/systemone"
        resp = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        answers_map = {}
        raw_answers = data.get("answers", {})

        if isinstance(raw_answers, dict):
            for name, item in raw_answers.items():
                if isinstance(item, dict):
                    probs = item.get("probabilities", {})
                    choice_name = item.get("choice", "Neutral")
                    answers_map[name] = ChoiceAnswer(choice=choice_name, probabilities=probs)
        elif isinstance(raw_answers, list):
            for item in raw_answers:
                if isinstance(item, dict):
                    name = item.get("name", "direction")
                    probs = item.get("probabilities", {})
                    choice_name = item.get("choice", "Neutral")
                    answers_map[name] = ChoiceAnswer(choice=choice_name, probabilities=probs)

        if "direction" not in answers_map and answers_map:
            first_key = next(iter(answers_map))
            answers_map["direction"] = answers_map[first_key]

        return SystemOneResponse(choices=answers_map, raw=data)


# Backward-compatible alias for existing imports
TypeSafeClient = CLMClient
