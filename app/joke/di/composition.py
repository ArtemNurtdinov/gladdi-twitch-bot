from sqlalchemy.orm import Session

from app.core.logger.di.composition import get_logger
from app.joke.application.usecase.get_jokes_configuration_use_case import GetJokesConfigurationUseCase
from app.joke.application.usecase.joke_use_case import JokeUseCase
from app.joke.application.usecase.save_jokes_configuration_use_case import SaveJokesConfigurationUseCase
from app.joke.di.dependencies import (
    provide_get_jokes_configuration_use_case,
    provide_joke_service,
    provide_joke_settings_repository,
    provide_joke_use_case,
    provide_jokes_configuration_mapper,
    provide_jokes_configuration_mapper_dto,
    provide_jokes_configuration_repository,
    provide_save_jokes_configuration_use_case,
)


def get_joke_use_case() -> JokeUseCase:
    logger = get_logger()
    joke_settings_repository = provide_joke_settings_repository(logger)
    joke_service = provide_joke_service(joke_settings_repository, logger)
    return provide_joke_use_case(joke_service)


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
