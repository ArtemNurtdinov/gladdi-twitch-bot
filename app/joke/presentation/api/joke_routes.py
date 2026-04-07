from fastapi import APIRouter, Depends, Query

from app.core.network.api.model.base_response import BaseResponse
from app.joke.di.composition import get_jokes_configuration_use_case, get_save_jokes_configuration_use_case
from app.joke.di.dependencies import provide_jokes_configuration_mapper_schema
from app.joke.presentation.api.mapper.jokes_configuration_mapper import JokesConfigurationMapper
from app.joke.presentation.api.model.configuration import JokesConfigurationSchema
from app.joke.presentation.api.model.response.configuration import JokesConfigurationResponse
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
