from app.core.logger.di.composition import get_logger
from app.joke.application.usecase.joke_use_case import JokeUseCase
from app.joke.di.dependencies import provide_joke_service, provide_joke_settings_repository, provide_joke_use_case


def get_joke_use_case() -> JokeUseCase:
    logger = get_logger()
    joke_settings_repository = provide_joke_settings_repository(logger)
    joke_service = provide_joke_service(joke_settings_repository, logger)
    return provide_joke_use_case(joke_service)
