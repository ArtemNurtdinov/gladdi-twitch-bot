from fastapi import Depends
from sqlalchemy.orm import Session

from core.db import get_db_ro, get_db_rw
from app.chat.data.chat_repository import ChatRepositoryImpl
from app.chat.application.chat_use_case import ChatUseCase


def get_chat_repo_ro(db: Session = Depends(get_db_ro)) -> ChatRepositoryImpl:
    return ChatRepositoryImpl(db)


def get_chat_repo_rw(db: Session = Depends(get_db_rw)) -> ChatRepositoryImpl:
    return ChatRepositoryImpl(db)


def get_chat_use_case_ro(repo: ChatRepositoryImpl = Depends(get_chat_repo_ro)) -> ChatUseCase:
    return ChatUseCase(repo)


def get_chat_use_case_rw(repo: ChatRepositoryImpl = Depends(get_chat_repo_rw)) -> ChatUseCase:
    return ChatUseCase(repo)

