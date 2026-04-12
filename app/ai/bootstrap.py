from dataclasses import dataclass

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.conversation.infrastructure.conversation_repository import ConversationRepositoryImpl
from app.ai.gen.prompt.prompt_service import PromptService
from core.provider import Provider


@dataclass
class AIProviders:
    prompt_service: PromptService
    conversation_service_provider: Provider[ConversationService]
    conversation_repo_provider: Provider[ConversationRepositoryImpl]


def build_ai_providers() -> AIProviders:
    prompt_service = PromptService()

    def conversation_service(db):
        return ConversationService(ConversationRepositoryImpl(db))

    def conversation_repo(db):
        return ConversationRepositoryImpl(db)

    return AIProviders(
        prompt_service=prompt_service,
        conversation_service_provider=Provider(conversation_service),
        conversation_repo_provider=Provider(conversation_repo),
    )
