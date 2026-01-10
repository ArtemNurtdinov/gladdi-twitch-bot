from dataclasses import dataclass

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.conversation.infrastructure.conversation_repository import ConversationRepositoryImpl
from app.ai.gen.llm.domain.llm_client_port import LLMClientPort
from app.ai.gen.llm.infrastructure.llm_box_client import LLMBoxClientPortImpl
from app.ai.gen.prompt.prompt_service import PromptService
from app.ai.intent.application.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.data.intent_detector_client import IntentDetectorClientImpl
from core.config import Config
from core.provider import Provider


@dataclass
class AIProviders:
    llm_client: LLMClientPort
    intent_detector: IntentDetectorClientImpl
    get_intent_use_case: GetIntentFromTextUseCase
    prompt_service: PromptService
    conversation_service_provider: Provider[ConversationService]
    conversation_repo_provider: Provider[ConversationRepositoryImpl]


def build_ai_providers(config: Config) -> AIProviders:
    llm_client = LLMBoxClientPortImpl(config.llmbox.host)
    intent_detector = IntentDetectorClientImpl()
    get_intent_from_text_use_case = GetIntentFromTextUseCase(intent_detector, llm_client)
    prompt_service = PromptService()

    def conversation_service(db):
        return ConversationService(ConversationRepositoryImpl(db))

    def conversation_repo(db):
        return ConversationRepositoryImpl(db)

    return AIProviders(
        llm_client=llm_client,
        intent_detector=intent_detector,
        get_intent_use_case=get_intent_from_text_use_case,
        prompt_service=prompt_service,
        conversation_service_provider=Provider(conversation_service),
        conversation_repo_provider=Provider(conversation_repo),
    )
