from contextlib import AbstractContextManager
from typing import Any, Protocol

from sqlalchemy.orm import Session


class SessionFactory(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> AbstractContextManager[Session]: ...
