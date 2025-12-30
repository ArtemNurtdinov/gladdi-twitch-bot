from typing import Callable, Generic, Optional, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class Provider(Generic[T]):

    def __init__(self, factory: Callable[[Session], T]):
        self._factory = factory

    def get(self, db: Session) -> T:
        return self._factory(db)


class SingletonProvider(Generic[T]):

    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._instance: Optional[T] = None

    def get(self) -> T:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance
