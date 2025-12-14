from fastapi import APIRouter, HTTPException
from features.joke.joke_schemas import JokesStatus, JokesResponse, JokesIntervalInfo, JokesIntervalResponse, JokesIntervalRequest
from features.joke.joke_service import JokeService
from features.joke.settings_manager import SettingsManager

router = APIRouter()


def get_joke_service() -> JokeService:
    settings_manager = SettingsManager()
    return JokeService(settings_manager)


@router.get(
    "/jokes/status",
    response_model=JokesStatus,
    summary="Статус анекдотов",
    description="Получить текущий статус включения/отключения анекдотов в Twitch боте",
    tags=["Bot Control"]
)
async def get_jokes_status() -> JokesStatus:
    try:
        joke_service = get_joke_service()
        return joke_service.get_jokes_status()
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
        joke_service = get_joke_service()
        return joke_service.enable_jokes()
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
        joke_service = get_joke_service()
        return joke_service.disable_jokes()
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
        joke_service = get_joke_service()
        return joke_service.get_jokes_interval()
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

        joke_service = get_joke_service()
        return joke_service.set_jokes_interval(request.min_minutes, request.max_minutes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка установки интервала анекдотов: {str(e)}")
