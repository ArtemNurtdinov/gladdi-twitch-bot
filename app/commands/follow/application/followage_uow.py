from __future__ import annotations

from typing import Protocol

from app.commands.follow.application.followage_port import FollowagePort
from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory


class FollowageUnitOfWork(UnitOfWork, Protocol):
    @property
    def followage_port(self) -> FollowagePort: ...


class FollowageUnitOfWorkFactory(UnitOfWorkFactory[FollowageUnitOfWork], Protocol):
    pass
