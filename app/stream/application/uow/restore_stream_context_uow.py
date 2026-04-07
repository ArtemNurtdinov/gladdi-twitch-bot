from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.stream.domain.repo import StreamRepository


class RestoreStreamContextUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_repository(self) -> StreamRepository: ...


class RestoreStreamContextUnitOfWorkFactory(UnitOfWorkFactory[RestoreStreamContextUnitOfWork], Protocol):
    pass
