from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.stream.domain.repo import StreamRepository


class StartNewStreamUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_repo(self) -> StreamRepository: ...


class StartNewStreamUnitOfWorkFactory(UnitOfWorkFactory[StartNewStreamUnitOfWork], Protocol):
    pass
