from fastapi import APIRouter, HTTPException
from features.joke.data.joke_schemas import JokesStatus, JokesResponse, JokesIntervalResponse, JokesIntervalRequest, NextJoke, JokeInterval
from features.joke.joke_service import JokeService
from features.joke.settings_repository import FileJokeSettingsRepository

router = APIRouter()


def get_joke_service() -> JokeService:
    settings_repo = FileJokeSettingsRepository()
    return JokeService(settings_repo)


def _to_next_joke_model(dto_next) -> NextJoke | None:
    if dto_next is None:
        return None
    return NextJoke(next_joke_time=dto_next.next_joke_time, minutes_until_next=dto_next.minutes_until_next)


def _to_interval_model(dto_interval) -> JokeInterval:
    return JokeInterval(
        min_minutes=dto_interval.min_minutes,
        max_minutes=dto_interval.max_minutes,
        description=dto_interval.description,
    )


@router.get(
    "/jokes/status",
    response_model=JokesStatus,
    summary="Статус анекдотов",
    description="Получить текущий статус включения/отключения анекдотов в Twitch боте"
)
async def get_jokes_status() -> JokesStatus:
    try:
        joke_service = get_joke_service()
        dto = joke_service.get_jokes_status()
        return JokesStatus(
            enabled=dto.enabled,
            message=dto.message,
            interval=_to_interval_model(dto.interval),
            next_joke=_to_next_joke_model(dto.next_joke),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса анекдотов: {str(e)}")


@router.post(
    "/jokes/enable",
    response_model=JokesResponse,
    summary="Включить анекдоты",
    description="Включить анекдоты в Twitch боте"
)
async def enable_jokes() -> JokesResponse:
    try:
        joke_service = get_joke_service()
        dto = joke_service.enable_jokes()
        return JokesResponse(success=dto.success, message=dto.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка включения анекдотов: {str(e)}")


@router.post(
    "/jokes/disable",
    response_model=JokesResponse,
    summary="Отключить анекдоты",
    description="Отключить анекдоты в Twitch боте"
)
async def disable_jokes() -> JokesResponse:
    try:
        joke_service = get_joke_service()
        dto = joke_service.disable_jokes()
        return JokesResponse(success=dto.success, message=dto.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отключения анекдотов: {str(e)}")


@router.post(
    "/jokes/interval",
    response_model=JokesIntervalResponse,
    summary="Установить интервал между анекдотами",
    description="Установить интервал между генерацией анекдотов в минутах. Бот будет генерировать анекдоты через случайное время от min_minutes до max_minutes"
)
async def set_jokes_interval(request: JokesIntervalRequest) -> JokesIntervalResponse:
    try:
        joke_service = get_joke_service()
        dto = joke_service.set_jokes_interval(request.min_minutes, request.max_minutes)
        return JokesIntervalResponse(
            success=dto.success,
            min_minutes=dto.min_minutes,
            max_minutes=dto.max_minutes,
            description=dto.description,
            next_joke=_to_next_joke_model(dto.next_joke),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка установки интервала анекдотов: {str(e)}")
