from abc import ABC, abstractmethod

from app.core.config.domain.model.configuration import Config


class ConfigRepository(ABC):
    @abstractmethod
    def get_config(self) -> Config: ...
