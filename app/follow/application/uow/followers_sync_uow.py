from __future__ import annotations

from typing import Protocol

from app.common.application.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.follow.domain.repo import FollowersRepository


class FollowersSyncUnitOfWork(UnitOfWork, Protocol):
    @property
    def followers_repo(self) -> FollowersRepository: ...


class FollowersSyncUnitOfWorkFactory(UnitOfWorkFactory[FollowersSyncUnitOfWork], Protocol):
    pass
