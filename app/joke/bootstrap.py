from dataclasses import dataclass

from app.joke.domain.joke_service import JokeService
from app.joke.infrastructure.settings_repository import FileJokeSettingsRepository


@dataclass
class JokeProviders:
    joke_service: JokeService


def build_joke_providers() -> JokeProviders:
    return JokeProviders(joke_service=JokeService(FileJokeSettingsRepository()))
