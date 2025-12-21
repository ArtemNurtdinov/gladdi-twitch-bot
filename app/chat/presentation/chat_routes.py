from datetime import datetime
from dataclasses import asdict

from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from core.db import get_db_ro, get_db_rw
from app.chat.presentation.chat_schemas import TopChatUsersResponse, TopChatUser
from app.chat.domain.chat_service import ChatService
from app.chat.data.chat_repository import ChatRepositoryImpl

router = APIRouter()


def get_chat_repo_ro(db: Session = Depends(get_db_ro)) -> ChatRepositoryImpl:
    return ChatRepositoryImpl(db)


def get_chat_repo_rw(db: Session = Depends(get_db_rw)) -> ChatRepositoryImpl:
    return ChatRepositoryImpl(db)


def get_chat_service_ro(repo: ChatRepositoryImpl = Depends(get_chat_repo_ro)) -> ChatService:
    return ChatService(repo)


def get_chat_service_rw(repo: ChatRepositoryImpl = Depends(get_chat_repo_rw)) -> ChatService:
    return ChatService(repo)


@router.get(
    "/top-users",
    response_model=TopChatUsersResponse,
    summary="Топ активных пользователей",
    description="Получить список самых активных пользователей"
)
async def get_top_users(
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество пользователей в результате"),
    date_from: datetime | None = Query(None, description="Начало периода (UTC)"),
    date_to: datetime | None = Query(None, description="Конец периода (UTC)"),
    chat_service: ChatService = Depends(get_chat_service_ro)
) -> TopChatUsersResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")
    users = chat_service.get_top_chat_users(limit, date_from, date_to)
    return TopChatUsersResponse(top_users=[TopChatUser(**asdict(user)) for user in users])
