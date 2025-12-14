from fastapi import APIRouter, Query, HTTPException
from typing import List
from features.dashboard.dashboard_schemas import TopUser, JokesStatus, JokesResponse, JokesIntervalInfo, JokesIntervalResponse, JokesIntervalRequest
from features.dashboard.dashboard_service import DashboardService
from features.dashboard.bot_control_service import BotControlService

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


@router.get(
    "/jokes/status",
    response_model=JokesStatus,
    summary="Статус анекдотов",
    description="Получить текущий статус включения/отключения анекдотов в Twitch боте",
    tags=["Bot Control"]
)
async def get_jokes_status() -> JokesStatus:
    try:
        bot_service = BotControlService()
        status = bot_service.get_jokes_status()
        return JokesStatus(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса анекдотов: {str(e)}")


@router.post(
    "/jokes/enable",
    response_model=JokesResponse,
    summary="Включить анекдоты",
    description="Включить анекдоты в Twitch боте",
    tags=["Bot Control"]
)
async def enable_jokes() -> JokesResponse:
    try:
        bot_service = BotControlService()
        result = bot_service.enable_jokes()
        return JokesResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка включения анекдотов: {str(e)}")


@router.post(
    "/jokes/disable",
    response_model=JokesResponse,
    summary="Отключить анекдоты",
    description="Отключить анекдоты в Twitch боте",
    tags=["Bot Control"]
)
async def disable_jokes() -> JokesResponse:
    try:
        bot_service = BotControlService()
        result = bot_service.disable_jokes()
        return JokesResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отключения анекдотов: {str(e)}")


@router.get(
    "/jokes/interval",
    response_model=JokesIntervalInfo,
    summary="Получить интервал между анекдотами",
    description="Получить текущий интервал между генерацией анекдотов в минутах",
    tags=["Bot Control"]
)
async def get_jokes_interval() -> JokesIntervalInfo:
    try:
        bot_service = BotControlService()
        result = bot_service.get_jokes_interval()
        return JokesIntervalInfo(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения интервала анекдотов: {str(e)}")


@router.post(
    "/jokes/interval",
    response_model=JokesIntervalResponse,
    summary="Установить интервал между анекдотами",
    description="Установить интервал между генерацией анекдотов в минутах. Бот будет генерировать анекдоты через случайное время от min_minutes до max_minutes",
    tags=["Bot Control"]
)
async def set_jokes_interval(request: JokesIntervalRequest) -> JokesIntervalResponse:
    try:
        if request.min_minutes > request.max_minutes:
            raise HTTPException(status_code=400, detail=f"Минимальный интервал ({request.min_minutes}) не может быть больше максимального ({request.max_minutes})")

        bot_service = BotControlService()
        result = bot_service.set_jokes_interval(request.min_minutes, request.max_minutes)
        return JokesIntervalResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка установки интервала анекдотов: {str(e)}")
