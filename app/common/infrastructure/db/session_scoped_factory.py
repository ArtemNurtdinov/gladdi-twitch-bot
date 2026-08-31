from collections.abc import Callable
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class SessionScopedFactory(Generic[T]):
    def __init__(self, factory: Callable[[Session], T]) -> None:
        self._factory = factory

    def get(self, db: Session) -> T:
        return self._factory(db)

    def __call__(self, db: Session) -> T:
        return self.get(db)
