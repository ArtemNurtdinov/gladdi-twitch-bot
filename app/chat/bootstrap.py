from dataclasses import dataclass

from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.chat.infrastructure.uow.chat_use_case_uow import SqlAlchemyChatUseCaseUnitOfWorkFactory
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


@dataclass
class ChatProviders:
    chat_use_case_provider: Provider[ChatUseCase]
    chat_repo_provider: Provider[ChatRepository]


def build_chat_providers() -> ChatProviders:
    def chat_repo(db):
        return ChatRepositoryImpl(db)

    def chat_use_case(db):
        return ChatUseCase(
            unit_of_work_factory=SqlAlchemyChatUseCaseUnitOfWorkFactory(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                chat_repo_provider=Provider(chat_repo),
            )
        )

    return ChatProviders(
        chat_use_case_provider=Provider(chat_use_case),
        chat_repo_provider=Provider(chat_repo),
    )


def get_chat_use_case_ro() -> ChatUseCase:
    def chat_repo(db):
        return ChatRepositoryImpl(db)

    return ChatUseCase(
        unit_of_work_factory=SqlAlchemyChatUseCaseUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            chat_repo_provider=Provider(chat_repo),
        )
    )
