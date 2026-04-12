from dataclasses import dataclass

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.conversation.infrastructure.conversation_repository import ConversationRepositoryImpl
from core.provider import Provider


@dataclass
class AIProviders:
    conversation_service_provider: Provider[ConversationService]
    conversation_repo_provider: Provider[ConversationRepositoryImpl]


def build_ai_providers() -> AIProviders:
    def conversation_service(db):
        return ConversationService(ConversationRepositoryImpl(db))

    def conversation_repo(db):
        return ConversationRepositoryImpl(db)

    return AIProviders(
        conversation_service_provider=Provider(conversation_service),
        conversation_repo_provider=Provider(conversation_repo),
    )
