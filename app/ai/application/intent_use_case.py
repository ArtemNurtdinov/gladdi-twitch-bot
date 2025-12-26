from app.ai.domain.intent_detector import IntentDetectorClient
from app.ai.domain.llm_client import LLMClient
from app.ai.domain.models import Intent


class IntentUseCase:

    def __init__(self, intent_detector: IntentDetectorClient, llm_client: LLMClient):
        self._intent_detector = intent_detector
        self._llm_client = llm_client

    def get_intent_from_text(self, text: str) -> Intent:
        detected_intent = self._intent_detector.extract_intent_from_text(text)
        if detected_intent in (Intent.HELLO, Intent.DANKAR_CUT, Intent.JACKBOX):
            return self._intent_detector.validate_intent_via_llm(detected_intent, text, self._llm_client)
        return detected_intent




