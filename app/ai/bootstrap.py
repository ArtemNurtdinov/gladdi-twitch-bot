from dataclasses import dataclass

from app.ai.gen.data.message_repository import ConversationRepositoryImpl
from app.ai.gen.domain.conversation_service import ConversationService
from app.ai.gen.domain.llm_client_port import LLMClientPort
from app.ai.gen.domain.prompt_service import PromptService
from app.ai.gen.infrastructure.llm_box_client import LLMBoxClientPortImpl
from app.ai.intent.application.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.data.intent_detector_client import IntentDetectorClientImpl
from core.provider import Provider


@dataclass
class AIProviders:
    llm_client: LLMClientPort
    intent_detector: IntentDetectorClientImpl
    get_intent_use_case: GetIntentFromTextUseCase
    prompt_service: PromptService
    conversation_service_provider: Provider[ConversationService]


def build_ai_providers() -> AIProviders:
    llm_client = LLMBoxClientPortImpl()
    intent_detector = IntentDetectorClientImpl()
    get_intent_from_text_use_case = GetIntentFromTextUseCase(intent_detector, llm_client)
    prompt_service = PromptService()

    def conversation_service(db):
        return ConversationService(ConversationRepositoryImpl(db))

    return AIProviders(
        llm_client=llm_client,
        intent_detector=intent_detector,
        get_intent_use_case=get_intent_from_text_use_case,
        prompt_service=prompt_service,
        conversation_service_provider=Provider(conversation_service),
    )
