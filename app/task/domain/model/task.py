from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass
class Task:
    name: str
    factory: Callable[[], Awaitable[None]]
