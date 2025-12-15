from fastapi import APIRouter, Query, HTTPException
from typing import List
from features.chat.chat_schemas import TopChatUser
from features.chat.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()

@router.get(
    "/top-users",
    response_model=List[TopChatUser],
    summary="Топ активных пользователей",
    description="Получить список самых активных пользователей"
)
async def get_top_users(
    channel_name: str,
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа"),
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество пользователей в результате")
) -> List[TopChatUser]:
    try:
        return chat_service.get_top_chat_users(channel_name, days, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения топ пользователей: {str(e)}")