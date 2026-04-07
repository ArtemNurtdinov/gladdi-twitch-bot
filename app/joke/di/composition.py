from sqlalchemy.orm import Session

from app.joke.application.usecase.get_jokes_configuration_use_case import GetJokesConfigurationUseCase
from app.joke.application.usecase.save_jokes_configuration_use_case import SaveJokesConfigurationUseCase
from app.joke.di.dependencies import (
    provide_get_jokes_configuration_use_case,
    provide_jokes_configuration_mapper,
    provide_jokes_configuration_mapper_dto,
    provide_jokes_configuration_repository,
    provide_save_jokes_configuration_use_case,
)


def get_jokes_configuration_use_case(session: Session) -> GetJokesConfigurationUseCase:
    mapper = provide_jokes_configuration_mapper()
    jokes_configuration_repository = provide_jokes_configuration_repository(session, mapper)
    mapper_dto = provide_jokes_configuration_mapper_dto()
    return provide_get_jokes_configuration_use_case(jokes_configuration_repository, mapper_dto)


def get_save_jokes_configuration_use_case(session: Session) -> SaveJokesConfigurationUseCase:
    mapper = provide_jokes_configuration_mapper()
    jokes_configuration_repository = provide_jokes_configuration_repository(session, mapper)
    mapper_dto = provide_jokes_configuration_mapper_dto()
    return provide_save_jokes_configuration_use_case(jokes_configuration_repository, mapper_dto)
