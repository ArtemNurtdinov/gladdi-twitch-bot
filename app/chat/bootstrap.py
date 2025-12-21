from fastapi import Depends
from sqlalchemy.orm import Session

from core.db import get_db_ro, get_db_rw
from app.chat.data.chat_repository import ChatRepositoryImpl
from app.chat.domain.chat_service import ChatService


def get_chat_repo_ro(db: Session = Depends(get_db_ro)) -> ChatRepositoryImpl:
    return ChatRepositoryImpl(db)


def get_chat_repo_rw(db: Session = Depends(get_db_rw)) -> ChatRepositoryImpl:
    return ChatRepositoryImpl(db)


def get_chat_service_ro(repo: ChatRepositoryImpl = Depends(get_chat_repo_ro)) -> ChatService:
    return ChatService(repo)


def get_chat_service_rw(repo: ChatRepositoryImpl = Depends(get_chat_repo_rw)) -> ChatService:
    return ChatService(repo)

