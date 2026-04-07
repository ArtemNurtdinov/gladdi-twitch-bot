from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.repo import StreamRepository
from app.viewer.session.domain.repository import ViewerRepository


class ViewerTimeUnitOfWork(UnitOfWork, Protocol):
    @property
    def viewer_repository(self) -> ViewerRepository: ...

    @property
    def economy_policy(self) -> EconomyPolicy: ...

    @property
    def stream_repository(self) -> StreamRepository: ...


class ViewerTimeUnitOfWorkFactory(UnitOfWorkFactory[ViewerTimeUnitOfWork], Protocol):
    pass
