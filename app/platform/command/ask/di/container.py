from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.chat.domain.repo import ChatRepository
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.platform.command.ask.application.ask_uow import AskUnitOfWorkFactory
from app.platform.command.ask.infrastructure.ask_uow import SqlAlchemyAskUnitOfWorkFactory
from core.types import SessionFactory


class AskContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro

    def ask_uow_factory(
        self,
        chat_repository_factory: SessionScopedFactory[ChatRepository],
        conversation_service_factory: SessionScopedFactory[ConversationService],
        system_prompt_repository_factory: SessionScopedFactory[SystemPromptRepository],
    ) -> AskUnitOfWorkFactory:
        return SqlAlchemyAskUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            chat_repository_factory=chat_repository_factory,
            conversation_service_factory=conversation_service_factory,
            system_prompt_repository_factory=system_prompt_repository_factory,
        )
