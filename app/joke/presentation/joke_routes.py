from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException

from app.joke.application.contracts import (
    JokeInterval,
    JokesIntervalRequest,
    JokesIntervalResponse,
    JokesResponse,
    JokesStatus,
    NextJoke,
)
from app.joke.application.dto import JokeIntervalDto, JokesIntervalResultDto, JokesResponseDto, JokesStatusDto, NextJokeDto
from app.joke.application.joke_use_case import JokeUseCase
from app.joke.bootstrap import JokeProviders, build_joke_providers

router = APIRouter()


@lru_cache
def get_joke_providers() -> JokeProviders:
    return build_joke_providers()


def get_joke_use_case(providers: JokeProviders = Depends(get_joke_providers)) -> JokeUseCase:
    return providers.joke_use_case


def _to_next_joke_model(dto_next: NextJokeDto | None) -> NextJoke | None:
    if dto_next is None:
        return None
    return NextJoke(next_joke_time=dto_next.next_joke_time, minutes_until_next=dto_next.minutes_until_next)


def _to_interval_model(dto_interval: JokeIntervalDto) -> JokeInterval:
    return JokeInterval(
        min_minutes=dto_interval.min_minutes,
        max_minutes=dto_interval.max_minutes,
        description=dto_interval.description,
    )


@router.get(
    "/status",
    response_model=JokesStatus,
    summary="Статус анекдотов",
    description="Получить текущий статус включения/отключения анекдотов в Twitch боте",
)
async def get_jokes_status(joke_service: JokeUseCase = Depends(get_joke_use_case)) -> JokesStatus:
    try:
        dto: JokesStatusDto = joke_service.get_jokes_status()
        return JokesStatus(
            enabled=dto.enabled,
            message=dto.message,
            interval=_to_interval_model(dto.interval),
            next_joke=_to_next_joke_model(dto.next_joke),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса анекдотов: {str(e)}")


@router.post("/enable", response_model=JokesResponse, summary="Включить анекдоты", description="Включить анекдоты в Twitch боте")
async def enable_jokes(joke_service: JokeUseCase = Depends(get_joke_use_case)) -> JokesResponse:
    try:
        dto: JokesResponseDto = joke_service.enable_jokes()
        return JokesResponse(success=dto.success, message=dto.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка включения анекдотов: {str(e)}")


@router.post("/disable", response_model=JokesResponse, summary="Отключить анекдоты", description="Отключить анекдоты в Twitch боте")
async def disable_jokes(joke_service: JokeUseCase = Depends(get_joke_use_case)) -> JokesResponse:
    try:
        dto: JokesResponseDto = joke_service.disable_jokes()
        return JokesResponse(success=dto.success, message=dto.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отключения анекдотов: {str(e)}")


@router.post(
    "/interval",
    response_model=JokesIntervalResponse,
    summary="Установить интервал между анекдотами",
    description="Установить интервал между генерацией анекдотов в минутах. "
    "Бот будет генерировать анекдоты через случайное время от min_minutes до max_minutes",
)
async def set_jokes_interval(
    request: JokesIntervalRequest, joke_service: JokeUseCase = Depends(get_joke_use_case)
) -> JokesIntervalResponse:
    try:
        dto: JokesIntervalResultDto = joke_service.set_jokes_interval(request.min_minutes, request.max_minutes)
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
