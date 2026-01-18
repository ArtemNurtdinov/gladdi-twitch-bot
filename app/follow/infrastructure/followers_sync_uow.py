from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.follow.application.followers_sync_uow import FollowersSyncUnitOfWork, FollowersSyncUnitOfWorkFactory
from app.follow.domain.repo import FollowersRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyFollowersSyncUnitOfWork(SqlAlchemyUnitOfWorkBase, FollowersSyncUnitOfWork):
    def __init__(self, session: Session, followers_repo: FollowersRepository, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._followers_repo = followers_repo

    @property
    def followers_repo(self) -> FollowersRepository:
        return self._followers_repo


class SqlAlchemyFollowersSyncUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[FollowersSyncUnitOfWork], FollowersSyncUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        followers_repository_provider: Provider[FollowersRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._followers_repository_provider = followers_repository_provider

    def _build_uow(self, db: Session, read_only: bool) -> FollowersSyncUnitOfWork:
        return SqlAlchemyFollowersSyncUnitOfWork(
            session=db,
            followers_repo=self._followers_repository_provider.get(db),
            read_only=read_only,
        )
