from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager, contextmanager
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from core.types import SessionFactory

TUnitOfWork = TypeVar("TUnitOfWork", bound=UnitOfWork)


class SqlAlchemyUnitOfWorkBase(UnitOfWork):
    def __init__(self, session: Session, read_only: bool):
        self._session = session
        self._read_only = read_only

    def commit(self) -> None:
        if not self._read_only:
            self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


class SqlAlchemyUnitOfWorkFactory(UnitOfWorkFactory[TUnitOfWork], Generic[TUnitOfWork]):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        builder: Callable[[Session, bool], TUnitOfWork],
    ):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._builder = builder

    def create(self, read_only: bool = False) -> AbstractContextManager[TUnitOfWork]:
        session_factory = self._session_factory_ro if read_only else self._session_factory_rw

        @contextmanager
        def _ctx():
            with session_factory() as db:
                uow = self._builder(db, read_only)
                try:
                    yield uow
                    if not read_only:
                        uow.commit()
                except Exception:
                    uow.rollback()
                    raise

        return _ctx()
