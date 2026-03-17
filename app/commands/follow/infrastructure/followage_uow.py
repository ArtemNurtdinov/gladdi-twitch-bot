from __future__ import annotations

from contextlib import contextmanager

from app.commands.follow.application.followage_uow import FollowageUnitOfWork, FollowageUnitOfWorkFactory
from app.platform.domain.repository import PlatformRepository


class SimpleFollowageUnitOfWork(FollowageUnitOfWork):
    def __init__(self, platform_repository: PlatformRepository):
        self._platform_repository = platform_repository

    @property
    def platform_repository(self) -> PlatformRepository:
        return self._platform_repository

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


class SimpleFollowageUnitOfWorkFactory(FollowageUnitOfWorkFactory):
    def __init__(self, platform_repository: PlatformRepository):
        self._platform_repository = platform_repository

    def create(self, read_only: bool = False):
        @contextmanager
        def _ctx():
            yield SimpleFollowageUnitOfWork(self._platform_repository)

        return _ctx()
