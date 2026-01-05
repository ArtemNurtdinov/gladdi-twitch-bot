from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.chat.data.chat_repository import ChatRepositoryImpl
from app.chat.domain.repo import ChatRepository
from core.db import get_db_ro, get_db_rw
from core.provider import Provider


@dataclass
class ChatProviders:
    chat_use_case_provider: Provider[ChatUseCase]
    chat_repo_provider: Provider[ChatRepository]


def build_chat_providers() -> ChatProviders:
    def chat_use_case(db):
        return ChatUseCase(ChatRepositoryImpl(db))

    def chat_repo(db):
        return ChatRepositoryImpl(db)

    return ChatProviders(
        chat_use_case_provider=Provider(chat_use_case),
        chat_repo_provider=Provider(chat_repo),
    )


def get_chat_repo_ro(db: Session = Depends(get_db_ro)) -> ChatRepositoryImpl:
    return ChatRepositoryImpl(db)


def get_chat_repo_rw(db: Session = Depends(get_db_rw)) -> ChatRepositoryImpl:
    return ChatRepositoryImpl(db)


def get_chat_use_case_ro(repo: ChatRepositoryImpl = Depends(get_chat_repo_ro)) -> ChatUseCase:
    return ChatUseCase(repo)


def get_chat_use_case_rw(repo: ChatRepositoryImpl = Depends(get_chat_repo_rw)) -> ChatUseCase:
    return ChatUseCase(repo)
