from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.repo import StreamRepository
from app.viewer.session.application.uow.viewer_time_uow import ViewerTimeUnitOfWork, ViewerTimeUnitOfWorkFactory
from app.viewer.session.domain.repository import ViewerRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyViewerTimeUnitOfWork(SqlAlchemyUnitOfWorkBase, ViewerTimeUnitOfWork):
    def __init__(
        self,
        session: Session,
        viewer_repository: ViewerRepository,
        economy_policy: EconomyPolicy,
        stream_repository: StreamRepository,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._viewer_repository = viewer_repository
        self._economy_policy = economy_policy
        self._stream_repository = stream_repository

    @property
    def viewer_repository(self) -> ViewerRepository:
        return self._viewer_repository

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def stream_repository(self) -> StreamRepository:
        return self._stream_repository


class SqlAlchemyViewerTimeUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[ViewerTimeUnitOfWork], ViewerTimeUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        stream_repository_factory: SessionScopedFactory[StreamRepository],
        viewer_repository_factory: SessionScopedFactory[ViewerRepository],
        economy_policy_provider: Provider[EconomyPolicy],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_repository_factory = stream_repository_factory
        self._viewer_repository_factory = viewer_repository_factory
        self._economy_policy_provider = economy_policy_provider

    def _build_uow(self, db: Session, read_only: bool) -> ViewerTimeUnitOfWork:
        return SqlAlchemyViewerTimeUnitOfWork(
            session=db,
            stream_repository=self._stream_repository_factory.get(db),
            viewer_repository=self._viewer_repository_factory.get(db),
            economy_policy=self._economy_policy_provider.get(db),
            read_only=read_only,
        )
