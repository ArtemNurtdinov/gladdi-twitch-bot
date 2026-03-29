from abc import ABC, abstractmethod


class ConfigSource(ABC):
    @abstractmethod
    def get_str(self, key: str, default: str | None = None) -> str | None: ...

    @abstractmethod
    def get_int(self, key: str, default: int | None = None) -> int | None: ...
