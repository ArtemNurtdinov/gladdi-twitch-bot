from contextlib import AbstractContextManager
from typing import Protocol

from sqlalchemy.orm import Session


class SessionFactory(Protocol):
    def __call__(self) -> AbstractContextManager[Session]: ...
