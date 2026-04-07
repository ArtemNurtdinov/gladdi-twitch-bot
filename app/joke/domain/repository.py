from abc import ABC, abstractmethod

from app.joke.domain.model.configuration import JokesConfiguration


class JokesConfigurationRepository(ABC):
    @abstractmethod
    async def get_current_configuration(self, channel_name: str) -> JokesConfiguration | None: ...

    @abstractmethod
    async def save_configuration(self, configuration: JokesConfiguration) -> None: ...
