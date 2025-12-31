from dataclasses import dataclass

from app.joke.data.settings_repository import FileJokeSettingsRepository
from app.joke.domain.joke_service import JokeService


@dataclass
class JokeProviders:
    joke_service: JokeService


def build_joke_providers() -> JokeProviders:
    return JokeProviders(joke_service=JokeService(FileJokeSettingsRepository()))
