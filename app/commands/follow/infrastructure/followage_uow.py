from __future__ import annotations

from contextlib import contextmanager

from app.commands.follow.application.followage_port import FollowagePort
from app.commands.follow.application.followage_uow import FollowageUnitOfWork, FollowageUnitOfWorkFactory


class SimpleFollowageUnitOfWork(FollowageUnitOfWork):
    def __init__(self, followage_port: FollowagePort):
        self._followage_port = followage_port

    @property
    def followage_port(self) -> FollowagePort:
        return self._followage_port

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None


class SimpleFollowageUnitOfWorkFactory(FollowageUnitOfWorkFactory):
    def __init__(self, followage_port: FollowagePort):
        self._followage_port = followage_port

    def create(self, read_only: bool = False):
        @contextmanager
        def _ctx():
            yield SimpleFollowageUnitOfWork(self._followage_port)

        return _ctx()
