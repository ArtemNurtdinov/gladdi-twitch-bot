from typing import Protocol

from app.ai.gen.llm.domain.llm_client_port import LLMClientPort
from app.ai.intent.domain.models import Intent


class IntentDetectorClient(Protocol):
    def extract_intent_from_text(self, text: str) -> Intent: ...

    async def validate_intent_via_llm(self, detected_intent: Intent, text: str, llm_client: LLMClientPort) -> Intent: ...
