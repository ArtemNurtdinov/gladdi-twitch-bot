from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session

from core.db import get_db
from dataclasses import asdict
from features.chat.data.chat_schemas import TopChatUsersResponse, TopChatUser
from features.chat.chat_service import ChatService
from features.chat.data.chat_repository import ChatRepositoryImpl

router = APIRouter()
chat_service = ChatService(ChatRepositoryImpl())


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
    db: Session = Depends(get_db)
) -> TopChatUsersResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")
    users = chat_service.get_top_chat_users(db, limit, date_from, date_to)
    return TopChatUsersResponse(top_users=[TopChatUser(**asdict(user)) for user in users])
