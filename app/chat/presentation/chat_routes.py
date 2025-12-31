from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.chat.application.chat_use_case import ChatUseCase
from app.chat.bootstrap import get_chat_use_case_ro
from app.chat.presentation.chat_schemas import TopChatUser, TopChatUsersResponse

router = APIRouter()


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
    chat_use_case: ChatUseCase = Depends(get_chat_use_case_ro),
) -> TopChatUsersResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")
    try:
        users = chat_use_case.get_top_chat_users(limit, date_from, date_to)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TopChatUsersResponse(top_users=[TopChatUser(**asdict(user)) for user in users])
