from __future__ import annotations

from abc import ABC, abstractmethod


class Logger(ABC):
    @abstractmethod
    def log_debug(self, message: str): ...

    @abstractmethod
    def log_info(self, message: str): ...

    @abstractmethod
    def log_error(self, message: str): ...

    @abstractmethod
    def log_exception(self, message: str, exception: Exception): ...

    @abstractmethod
    def create_child(self, child_tag: str) -> Logger: ...
