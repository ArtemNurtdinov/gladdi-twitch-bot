from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from features.dashboard.dashboard_schemas import OverviewStats, HourlyActivity, DailyActivity, TopUser, BattleStats, AIInteractionStats, ActivityHeatmap, MessagesResponse, \
    JokesStatus, JokesResponse, JokesIntervalInfo, JokesIntervalResponse, JokesIntervalRequest, JokeGeneratedResponse, MythicalEvent, \
    BetHourlyActivity, LuckyUser, UserBalanceStats, TransactionStats, StreamStats, \
    StreamHistoryResponse, StreamInfo, CurrentStreamInfo, ViewerSessionStats, ViewerTopByTime, ViewerSessionRewards, ViewerSessionActivity
from features.dashboard.dashboard_service import DashboardService
from features.dashboard.bot_control_service import BotControlService

router = APIRouter()
analytics_service = DashboardService()


@router.get(
    "/overview",
    response_model=OverviewStats,
    summary="Общая статистика",
    description="Получить общую статистику активности за указанный период"
)
async def get_overview(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа (от 1 до 365)")) -> OverviewStats:
    try:
        data = analytics_service.get_overview_stats(days)
        return OverviewStats(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения общей статистики: {str(e)}")


@router.get(
    "/chat-activity-hourly",
    response_model=HourlyActivity,
    summary="Активность по часам",
    description="Получить распределение активности чата по часам суток"
)
async def get_chat_activity_hourly(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> HourlyActivity:
    try:
        data = analytics_service.get_chat_activity_by_hour(days)
        return HourlyActivity(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения активности по часам: {str(e)}")


@router.get(
    "/daily-activity",
    response_model=DailyActivity,
    summary="Ежедневная активность",
    description="Получить ежедневную активность пользователей и сообщений"
)
async def get_daily_activity(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> DailyActivity:
    try:
        data = analytics_service.get_daily_activity(days)
        return DailyActivity(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения ежедневной активности: {str(e)}")


@router.get(
    "/top-users",
    response_model=List[TopUser],
    summary="Топ активных пользователей",
    description="Получить список самых активных пользователей"
)
async def get_top_users(
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа"),
    limit: int = Query(10, ge=1, le=50, description="Максимальное количество пользователей в результате")
) -> List[TopUser]:
    try:
        data = analytics_service.get_top_users(days, limit)
        return [TopUser(**user) for user in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения топ пользователей: {str(e)}")


@router.get(
    "/battle-stats",
    response_model=BattleStats,
    summary="Статистика битв",
    description="Получить статистику битв, включая топ победителей и участников"
)
async def get_battle_stats(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> BattleStats:
    try:
        data = analytics_service.get_battle_statistics(days)
        return BattleStats(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики битв: {str(e)}")


@router.get(
    "/ai-interactions",
    response_model=AIInteractionStats,
    summary="AI взаимодействия",
    description="Получить статистику взаимодействий с AI ботом"
)
async def get_ai_interactions(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> AIInteractionStats:
    try:
        data = analytics_service.get_ai_interaction_stats(days)
        return AIInteractionStats(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики AI: {str(e)}")


@router.get(
    "/activity-heatmap",
    response_model=ActivityHeatmap,
    summary="Тепловая карта активности",
    description="Получить тепловую карту активности по дням недели и часам"
)
async def get_activity_heatmap(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> ActivityHeatmap:
    try:
        data = analytics_service.get_user_activity_heatmap(days)
        return ActivityHeatmap(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения тепловой карты: {str(e)}")


@router.get(
    "/chat-messages",
    response_model=MessagesResponse,
    summary="История сообщений чата",
    description="Получить историю сообщений чата с пагинацией и фильтрами"
)
async def get_chat_messages(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(50, ge=1, le=100, description="Количество сообщений на странице"),
    user_filter: Optional[str] = Query(None, description="Фильтр по имени пользователя"),
    date_from: Optional[str] = Query(None, description="Дата начала (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Дата окончания (YYYY-MM-DD)")
) -> MessagesResponse:
    try:
        date_from_parsed = None
        date_to_parsed = None

        if date_from:
            try:
                date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Неверный формат даты date_from. Используйте YYYY-MM-DD")

        if date_to:
            try:
                date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d")
                date_to_parsed = date_to_parsed.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(status_code=400, detail="Неверный формат даты date_to. Используйте YYYY-MM-DD")

        data = analytics_service.get_chat_messages(page, limit, user_filter, date_from_parsed, date_to_parsed)
        return MessagesResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения сообщений чата: {str(e)}")


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


@router.post(
    "/jokes/generated",
    response_model=JokeGeneratedResponse,
    summary="Отметить генерацию анекдота",
    description="Отметить, что анекдот был сгенерирован. Планирует время следующего анекдота",
    tags=["Bot Control"]
)
async def mark_joke_generated() -> JokeGeneratedResponse:
    try:
        bot_service = BotControlService()
        result = bot_service.mark_joke_generated()
        return JokeGeneratedResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отметки генерации анекдота: {str(e)}")


@router.get(
    "/bet-mythical-events",
    response_model=List[MythicalEvent],
    summary="Мифические события",
    description="Получить список всех мифических событий",
    tags=["Bet Analytics"]
)
async def get_bet_mythical_events(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> List[MythicalEvent]:
    try:
        data = analytics_service.get_mythical_events(days)
        return [MythicalEvent(**event) for event in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения мифических событий: {str(e)}")


@router.get(
    "/bet-activity-hourly",
    response_model=BetHourlyActivity,
    summary="Активность ставок по часам",
    description="Получить распределение активности ставок по часам суток",
    tags=["Bet Analytics"]
)
async def get_bet_activity_hourly(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> BetHourlyActivity:
    try:
        data = analytics_service.get_bet_hourly_activity(days)
        return BetHourlyActivity(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения активности ставок: {str(e)}")


@router.get(
    "/bet-lucky-users",
    response_model=List[LuckyUser],
    summary="Самые удачливые пользователи",
    description="Получить список самых удачливых пользователей (с высоким процентом джекпотов)",
    tags=["Bet Analytics"]
)
async def get_bet_lucky_users(
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа"),
    min_bets: int = Query(5, ge=1, le=100, description="Минимальное количество ставок для включения в рейтинг")
) -> List[LuckyUser]:
    try:
        data = analytics_service.get_lucky_users(days, min_bets)
        return [LuckyUser(**user) for user in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения удачливых пользователей: {str(e)}")


@router.get(
    "/economy/balance-stats",
    response_model=UserBalanceStats,
    summary="Статистика балансов",
    description="Получить статистику балансов пользователей",
    tags=["Economy Analytics"]
)
async def get_balance_stats(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> UserBalanceStats:
    try:
        data = analytics_service.get_user_balance_stats(days)
        return UserBalanceStats(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики балансов: {str(e)}")


@router.get(
    "/economy/transaction-stats",
    response_model=TransactionStats,
    summary="Статистика транзакций",
    description="Получить общую статистику транзакций",
    tags=["Economy Analytics"]
)
async def get_transaction_stats(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> TransactionStats:
    try:
        data = analytics_service.get_transaction_stats(days)
        return TransactionStats(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики транзакций: {str(e)}")


@router.get(
    "/stream-stats",
    response_model=StreamStats,
    summary="Статистика стримов",
    description="Получить общую статистику стримов за указанный период",
    tags=["Stream Analytics"]
)
async def get_stream_stats(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> StreamStats:
    try:
        data = analytics_service.get_stream_stats(days)
        return StreamStats(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики стримов: {str(e)}")


@router.get(
    "/stream-history",
    response_model=StreamHistoryResponse,
    summary="История стримов",
    description="Получить историю стримов с пагинацией",
    tags=["Stream Analytics"]
)
async def get_stream_history(
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(10, ge=1, le=50, description="Количество стримов на странице"),
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")
) -> StreamHistoryResponse:
    try:
        data = analytics_service.get_stream_history(page, limit, days)
        return StreamHistoryResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории стримов: {str(e)}")


@router.get(
    "/stream-top-by-duration",
    response_model=List[StreamInfo],
    summary="Топ стримов по длительности",
    description="Получить список стримов с наибольшей длительностью",
    tags=["Stream Analytics"]
)
async def get_stream_top_by_duration(
    limit: int = Query(10, ge=1, le=50, description="Максимальное количество стримов в результате"),
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")
) -> List[StreamInfo]:
    try:
        data = analytics_service.get_stream_top_by_duration(limit, days)
        return [StreamInfo(**stream) for stream in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения топа стримов по длительности: {str(e)}")


@router.get(
    "/stream-top-by-viewers",
    response_model=List[StreamInfo],
    summary="Топ стримов по зрителям",
    description="Получить список стримов с наибольшим количеством зрителей",
    tags=["Stream Analytics"]
)
async def get_stream_top_by_viewers(
    limit: int = Query(10, ge=1, le=50, description="Максимальное количество стримов в результате"),
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")
) -> List[StreamInfo]:
    try:
        data = analytics_service.get_stream_top_by_viewers(limit, days)
        return [StreamInfo(**stream) for stream in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения топа стримов по зрителям: {str(e)}")


@router.get(
    "/stream-current",
    response_model=Optional[CurrentStreamInfo],
    summary="Текущий стрим",
    description="Получить информацию о текущем активном стриме",
    tags=["Stream Analytics"]
)
async def get_current_stream() -> Optional[CurrentStreamInfo]:
    try:
        data = analytics_service.get_current_stream()
        if data:
            return CurrentStreamInfo(**data)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения текущего стрима: {str(e)}")


@router.get(
    "/viewer-session-stats",
    response_model=ViewerSessionStats,
    summary="Статистика сессий зрителей",
    description="Получить общую статистику сессий зрителей за указанный период",
    tags=["Viewer Session Analytics"]
)
async def get_viewer_session_stats(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> ViewerSessionStats:
    try:
        data = analytics_service.get_viewer_session_stats(days)
        return ViewerSessionStats(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики сессий зрителей: {str(e)}")


@router.get(
    "/viewer-top-by-time",
    response_model=List[ViewerTopByTime],
    summary="Топ зрителей по времени просмотра",
    description="Получить список зрителей с наибольшим временем просмотра",
    tags=["Viewer Session Analytics"]
)
async def get_viewer_top_by_time(
    limit: int = Query(10, ge=1, le=50, description="Максимальное количество зрителей в результате"),
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")
) -> List[ViewerTopByTime]:
    try:
        data = analytics_service.get_viewer_top_by_time(limit, days)
        return [ViewerTopByTime(**viewer) for viewer in data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения топа зрителей: {str(e)}")


@router.get(
    "/viewer-session-rewards",
    response_model=ViewerSessionRewards,
    summary="Статистика наград зрителей",
    description="Получить статистику по наградам, полученным зрителями",
    tags=["Viewer Session Analytics"]
)
async def get_viewer_session_rewards(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> ViewerSessionRewards:
    try:
        data = analytics_service.get_viewer_session_rewards(days)
        return ViewerSessionRewards(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики наград: {str(e)}")


@router.get(
    "/viewer-session-activity",
    response_model=ViewerSessionActivity,
    summary="Активность зрителей по времени",
    description="Получить распределение активности зрителей по часам и дням",
    tags=["Viewer Session Analytics"]
)
async def get_viewer_session_activity(days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")) -> ViewerSessionActivity:
    try:
        data = analytics_service.get_viewer_session_activity(days)
        return ViewerSessionActivity(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения активности зрителей: {str(e)}")
