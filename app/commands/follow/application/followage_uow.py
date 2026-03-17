from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.platform.domain.repository import PlatformRepository


class FollowageUnitOfWork(UnitOfWork, Protocol):
    @property
    def platform_repository(self) -> PlatformRepository: ...


class FollowageUnitOfWorkFactory(UnitOfWorkFactory[FollowageUnitOfWork], Protocol):
    pass
