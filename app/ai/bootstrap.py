from dataclasses import dataclass

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.conversation.infrastructure.conversation_repository import ConversationRepositoryImpl
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.llm.infrastructure.llm_repository import LLMRepositoryImpl
from app.ai.gen.prompt.infrastructure.system_prompt_repository import SystemPromptRepository, SystemPromptRepositoryImpl
from app.ai.gen.prompt.prompt_service import PromptService
from app.ai.intent.application.usecases.get_intent_use_case import GetIntentFromTextUseCase
from app.ai.intent.data.intent_detector_client import IntentDetectorClientImpl
from app.ai.intent.infrastructure.intent_uow import SimpleIntentUnitOfWorkFactory
from core.provider import Provider


@dataclass
class AIProviders:
    llm_repository: LLMRepository
    system_prompt_repo_provider: Provider[SystemPromptRepository]
    intent_detector: IntentDetectorClientImpl
    get_intent_use_case: GetIntentFromTextUseCase
    prompt_service: PromptService
    conversation_service_provider: Provider[ConversationService]
    conversation_repo_provider: Provider[ConversationRepositoryImpl]


def build_ai_providers(llmbox_host: str, intent_detector_host: str) -> AIProviders:
    llm_repository = LLMRepositoryImpl(llmbox_host)
    intent_detector = IntentDetectorClientImpl(intent_detector_host)
    get_intent_from_text_use_case = GetIntentFromTextUseCase(
        unit_of_work_factory=SimpleIntentUnitOfWorkFactory(intent_detector, llm_repository)
    )
    prompt_service = PromptService()

    def system_prompt_repo(db):
        return SystemPromptRepositoryImpl(db)

    def conversation_service(db):
        return ConversationService(ConversationRepositoryImpl(db))

    def conversation_repo(db):
        return ConversationRepositoryImpl(db)

    return AIProviders(
        llm_repository=llm_repository,
        system_prompt_repo_provider=Provider(system_prompt_repo),
        intent_detector=intent_detector,
        get_intent_use_case=get_intent_from_text_use_case,
        prompt_service=prompt_service,
        conversation_service_provider=Provider(conversation_service),
        conversation_repo_provider=Provider(conversation_repo),
    )
