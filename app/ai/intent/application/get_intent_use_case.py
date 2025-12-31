from app.ai.gen.domain.llm_client import LLMClient
from app.ai.intent.domain.intent_detector import IntentDetectorClient
from app.ai.intent.domain.models import Intent


class GetIntentFromTextUseCase:
    def __init__(self, intent_detector: IntentDetectorClient, llm_client: LLMClient):
        self._intent_detector = intent_detector
        self._llm_client = llm_client

    async def get_intent_from_text(self, text: str) -> Intent:
        detected_intent = self._intent_detector.extract_intent_from_text(text)
        if detected_intent in (Intent.HELLO, Intent.DANKAR_CUT, Intent.JACKBOX):
            return await self._intent_detector.validate_intent_via_llm(detected_intent, text, self._llm_client)
        return detected_intent
