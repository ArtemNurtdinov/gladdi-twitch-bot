from dataclasses import dataclass

from app.joke.application.joke_use_case import JokeUseCase
from app.joke.domain.joke_service import JokeService
from app.joke.infrastructure.settings_repository import FileJokeSettingsRepository


@dataclass
class JokeProviders:
    joke_service: JokeService
    joke_use_case: JokeUseCase


def build_joke_providers() -> JokeProviders:
    domain_service = JokeService(FileJokeSettingsRepository())
    return JokeProviders(
        joke_service=domain_service,
        joke_use_case=JokeUseCase(domain_service),
    )
