from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.network.api.model.base_response import BaseResponse
from app.joke.application.dto import JokeIntervalDto, JokesIntervalResultDto, JokesResponseDto, JokesStatusDto, NextJokeDto
from app.joke.application.usecase.joke_use_case import JokeUseCase
from app.joke.di.composition import get_joke_use_case, get_jokes_configuration_use_case, get_save_jokes_configuration_use_case
from app.joke.di.dependencies import provide_jokes_configuration_mapper_schema
from app.joke.presentation.api.mapper.jokes_configuration_mapper import JokesConfigurationMapper
from app.joke.presentation.api.model.configuration import JokesConfigurationSchema
from app.joke.presentation.api.model.response.configuration import JokesConfigurationResponse
from app.joke.presentation.model.interval import JokeIntervalSchema
from app.joke.presentation.model.next_joke import NextJokeSchema
from app.joke.presentation.model.request.interval import JokesIntervalRequest
from app.joke.presentation.model.response.interval import JokesIntervalResponse
from app.joke.presentation.model.response.jokes import JokesResponse
from app.joke.presentation.model.response.status import JokesStatusResponse
from core.db import db_ro_session, db_rw_session

router = APIRouter()


@router.get("/configuration", summary="Конфигурация анекдотов", response_model=JokesConfigurationResponse)
async def get_configuration(
    channel_name: str = Query(..., description="Имя канала"),
    mapper: JokesConfigurationMapper = Depends(provide_jokes_configuration_mapper_schema),
) -> JokesConfigurationResponse:
    with db_ro_session() as session:
        jokes_configuration_use_case = get_jokes_configuration_use_case(session)
        configuration = await jokes_configuration_use_case.get_configuration(channel_name=channel_name)
    configuration_schema = mapper.map_to_schema(configuration)
    return JokesConfigurationResponse(jokes_configuration=configuration_schema)


@router.post("/configuration", summary="Сохранить конфигурацию анекдотов", response_model=BaseResponse)
async def save_configuration(
    configuration: JokesConfigurationSchema,
    mapper: JokesConfigurationMapper = Depends(provide_jokes_configuration_mapper_schema),
) -> BaseResponse:
    configuration_dto = mapper.map_to_dto(configuration)
    with db_rw_session() as session:
        save_jokes_configuration_use_case = get_save_jokes_configuration_use_case(session)
        await save_jokes_configuration_use_case.save_configuration(configuration_dto)
    return BaseResponse(message="Конфигурация успешно сохранена")


def _to_next_joke_model(dto_next: NextJokeDto | None) -> NextJokeSchema | None:
    if dto_next is None:
        return None
    return NextJokeSchema(next_joke_time=dto_next.next_joke_time, minutes_until_next=dto_next.minutes_until_next)


def _to_interval_model(dto_interval: JokeIntervalDto) -> JokeIntervalSchema:
    return JokeIntervalSchema(
        min_minutes=dto_interval.min_minutes,
        max_minutes=dto_interval.max_minutes,
        description=dto_interval.description,
    )


@router.get("/status", summary="Статус анекдотов", response_model=JokesStatusResponse)
async def get_jokes_status(joke_service: JokeUseCase = Depends(get_joke_use_case)) -> JokesStatusResponse:
    try:
        joke_status: JokesStatusDto = joke_service.get_jokes_status()
        return JokesStatusResponse(
            enabled=joke_status.enabled,
            message=joke_status.message,
            interval=_to_interval_model(joke_status.interval),
            next_joke=_to_next_joke_model(joke_status.next_joke),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса анекдотов: {str(e)}")


@router.post("/enable", summary="Включить анекдоты", response_model=JokesResponse)
async def enable_jokes(joke_service: JokeUseCase = Depends(get_joke_use_case)) -> JokesResponse:
    try:
        jokes: JokesResponseDto = joke_service.enable_jokes()
        return JokesResponse(success=jokes.success, message=jokes.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка включения анекдотов: {str(e)}")


@router.post("/disable", summary="Отключить анекдоты", response_model=JokesResponse)
async def disable_jokes(joke_service: JokeUseCase = Depends(get_joke_use_case)) -> JokesResponse:
    try:
        dto: JokesResponseDto = joke_service.disable_jokes()
        return JokesResponse(success=dto.success, message=dto.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка отключения анекдотов: {str(e)}")


@router.post("/interval", summary="Установить интервал между анекдотами", response_model=JokesIntervalResponse)
async def set_jokes_interval(
    request: JokesIntervalRequest, joke_service: JokeUseCase = Depends(get_joke_use_case)
) -> JokesIntervalResponse:
    try:
        interval: JokesIntervalResultDto = joke_service.set_jokes_interval(request.min_minutes, request.max_minutes)
        return JokesIntervalResponse(
            success=interval.success,
            min_minutes=interval.min_minutes,
            max_minutes=interval.max_minutes,
            description=interval.description,
            next_joke=_to_next_joke_model(interval.next_joke),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка установки интервала анекдотов: {str(e)}")
