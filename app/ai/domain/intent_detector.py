from typing import Protocol

from app.ai.domain.models import Intent
from app.ai.domain.llm_client import LLMClient


class IntentDetectorClient(Protocol):
    def extract_intent_from_text(self, text: str) -> Intent:
        ...

    def validate_intent_via_llm(self, detected_intent: Intent, text: str, llm_client: LLMClient) -> Intent:
        ...

