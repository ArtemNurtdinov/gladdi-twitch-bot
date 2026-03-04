from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.stream_service import StreamService
from app.viewer.domain.repo import ViewerRepository


class ViewerTimeUnitOfWork(UnitOfWork, Protocol):
    @property
    def stream_service(self) -> StreamService: ...

    @property
    def viewer_repository(self) -> ViewerRepository: ...

    @property
    def economy_policy(self) -> EconomyPolicy: ...


class ViewerTimeUnitOfWorkFactory(UnitOfWorkFactory[ViewerTimeUnitOfWork], Protocol):
    pass
