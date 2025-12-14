from fastapi import APIRouter, Query, HTTPException
from typing import List
from features.dashboard.dashboard_schemas import TopUser
from features.dashboard.dashboard_service import DashboardService

router = APIRouter()
analytics_service = DashboardService()


@router.get(
    "/top-users",
    response_model=List[TopUser],
    summary="Топ активных пользователей",
    description="Получить список самых активных пользователей"
)
async def get_top_users(
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа"),
    limit: int = Query(10, ge=1, le=100, description="Максимальное количество пользователей в результате")
) -> List[TopUser]:
    try:
        data = analytics_service.get_top_users(days, limit)
        return [TopUser(**user) for user in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения топ пользователей: {str(e)}")


