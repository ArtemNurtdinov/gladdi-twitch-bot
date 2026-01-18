from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.domain.stream_service import StreamService
from app.viewer.application.viewer_time_uow import ViewerTimeUnitOfWork, ViewerTimeUnitOfWorkFactory
from app.viewer.domain.viewer_session_service import ViewerTimeService
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyViewerTimeUnitOfWork(SqlAlchemyUnitOfWorkBase, ViewerTimeUnitOfWork):
    def __init__(
        self,
        session: Session,
        viewer_service: ViewerTimeService,
        stream_service: StreamService,
        economy_policy: EconomyPolicy,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._viewer_service = viewer_service
        self._stream_service = stream_service
        self._economy_policy = economy_policy

    @property
    def viewer_service(self) -> ViewerTimeService:
        return self._viewer_service

    @property
    def stream_service(self) -> StreamService:
        return self._stream_service

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy


class SqlAlchemyViewerTimeUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[ViewerTimeUnitOfWork], ViewerTimeUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        viewer_service_provider: Provider[ViewerTimeService],
        stream_service_provider: Provider[StreamService],
        economy_policy_provider: Provider[EconomyPolicy],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._viewer_service_provider = viewer_service_provider
        self._stream_service_provider = stream_service_provider
        self._economy_policy_provider = economy_policy_provider

    def _build_uow(self, db: Session, read_only: bool) -> ViewerTimeUnitOfWork:
        return SqlAlchemyViewerTimeUnitOfWork(
            session=db,
            viewer_service=self._viewer_service_provider.get(db),
            stream_service=self._stream_service_provider.get(db),
            economy_policy=self._economy_policy_provider.get(db),
            read_only=read_only,
        )
