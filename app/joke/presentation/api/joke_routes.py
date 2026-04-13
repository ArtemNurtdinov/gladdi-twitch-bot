from fastapi import APIRouter, Query

from app.core.network.api.model.base_response import BaseResponse
from app.joke.di.container import JokeContainer
from app.joke.presentation.api.model.configuration import JokesConfigurationSchema
from app.joke.presentation.api.model.response.configuration import JokesConfigurationResponse
from core.db import db_ro_session, db_rw_session

router = APIRouter()


@router.get("/configuration", summary="Конфигурация анекдотов", response_model=JokesConfigurationResponse)
async def get_configuration(
    channel_name: str = Query(..., description="Имя канала"),
) -> JokesConfigurationResponse:
    joke_container = JokeContainer()
    with db_ro_session() as session:
        jokes_configuration_use_case = joke_container.get_jokes_configuration_use_case(session)
        configuration = await jokes_configuration_use_case.get_configuration(channel_name=channel_name)
    configuration_schema = joke_container.jokes_configuration_schema_mapper.map_to_schema(configuration)
    return JokesConfigurationResponse(jokes_configuration=configuration_schema)


@router.post("/configuration", summary="Сохранить конфигурацию анекдотов", response_model=BaseResponse)
async def save_configuration(
    configuration: JokesConfigurationSchema,
) -> BaseResponse:
    joke_container = JokeContainer()
    configuration_dto = joke_container.jokes_configuration_schema_mapper.map_to_dto(configuration)
    with db_rw_session() as session:
        save_jokes_configuration_use_case = joke_container.save_jokes_configuration_use_case(session)
        await save_jokes_configuration_use_case.save_configuration(configuration_dto)
    return BaseResponse(message="Конфигурация успешно сохранена")
