from typing import Protocol

from app.joke.domain.model.joke_settings import JokesSettings


class JokeSettingsRepository(Protocol):
    def load(self) -> JokesSettings: ...

    def save(self, settings: JokesSettings) -> JokesSettings: ...
