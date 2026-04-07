from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.chat.di.container import ChatContainer
from app.chat.presentation.schemas.chat_user import TopChatUser, TopChatUsersResponse
from app.core.logger.domain.logger import Logger
from core.db import db_ro_session, db_rw_session

router = APIRouter()


def get_logger(request: Request) -> Logger:
    return request.app.state.logger


@router.get(
    "/top-users",
    response_model=TopChatUsersResponse,
    summary="Топ активных пользователей",
    description="Получить список самых активных пользователей",
)
async def get_top_users(
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество пользователей в результате"),
    date_from: datetime | None = Query(None, description="Начало периода (UTC)"),
    date_to: datetime | None = Query(None, description="Конец периода (UTC)"),
    logger: Logger = Depends(get_logger),
) -> TopChatUsersResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")
    chat_container = ChatContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session, logger=logger)
    try:
        users = chat_container.chat_use_case().get_top_chat_users(limit, date_from, date_to)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TopChatUsersResponse(top_users=[TopChatUser(**asdict(user)) for user in users])
