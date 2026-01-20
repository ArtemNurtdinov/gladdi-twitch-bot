from app.ai.intent.application.intent_uow import IntentUnitOfWorkFactory
from app.ai.intent.domain.models import Intent


class GetIntentFromTextUseCase:
    def __init__(self, unit_of_work_factory: IntentUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    async def get_intent_from_text(self, text: str) -> Intent:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            detected_intent = uow.intent_detector.extract_intent_from_text(text)
            if detected_intent in (Intent.HELLO, Intent.DANKAR_CUT, Intent.JACKBOX):
                return await uow.intent_detector.validate_intent_via_llm(detected_intent, text, uow.llm_client)
            return detected_intent
