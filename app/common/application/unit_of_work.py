from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Generic, Protocol, TypeVar


class UnitOfWork(Protocol):
    def commit(self) -> None: ...

    def rollback(self) -> None: ...


TUnitOfWork = TypeVar("TUnitOfWork", bound=UnitOfWork)


class UnitOfWorkFactory(Protocol, Generic[TUnitOfWork]):
    def create(self, read_only: bool = False) -> AbstractContextManager[TUnitOfWork]: ...
