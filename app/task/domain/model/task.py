from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any


@dataclass
class Task:
    name: str
    factory: Callable[[], Coroutine[Any, Any, None]]
