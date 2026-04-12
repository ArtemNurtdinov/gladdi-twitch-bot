from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.chat.domain.repo import ChatRepository
from app.platform.command.ask.application.ask_uow import AskUnitOfWorkFactory
from app.platform.command.ask.infrastructure.ask_uow import SqlAlchemyAskUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


def provide_ask_uow_factory(
    session_factory_rw: SessionFactory,
    session_factory_ro: SessionFactory,
    chat_repository_provider: Provider[ChatRepository],
    conversation_service_provider: Provider[ConversationService],
    system_prompt_repository_provider: Provider[SystemPromptRepository],
) -> AskUnitOfWorkFactory:
    return SqlAlchemyAskUnitOfWorkFactory(
        session_factory_rw=session_factory_rw,
        session_factory_ro=session_factory_ro,
        chat_repo_provider=chat_repository_provider,
        conversation_service_provider=conversation_service_provider,
        system_prompt_repository_provider=system_prompt_repository_provider,
    )
