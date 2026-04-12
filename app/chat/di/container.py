from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.chat.infrastructure.uow.chat_use_case_uow import SqlAlchemyChatUseCaseUnitOfWorkFactory
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


def get_chat_use_case() -> ChatUseCase:
    return ChatUseCase(
        chat_uow_factory=SqlAlchemyChatUseCaseUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            chat_repo_provider=Provider(lambda session: ChatRepositoryImpl(session)),
        )
    )
