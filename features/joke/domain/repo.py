from typing import Protocol

from features.joke.domain.models import BotSettings


class JokeSettingsRepository(Protocol):

    def load(self) -> BotSettings:
        ...

    def save(self, settings: BotSettings) -> BotSettings:
        ...




