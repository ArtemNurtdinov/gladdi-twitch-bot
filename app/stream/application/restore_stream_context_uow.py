from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.stream.domain.stream_service import StreamService


class RestoreStreamContextUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_service(self) -> StreamService: ...


class RestoreStreamContextUnitOfWorkFactory(UnitOfWorkFactory[RestoreStreamContextUnitOfWork], Protocol):
    pass
