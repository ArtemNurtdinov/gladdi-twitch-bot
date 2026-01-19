from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.stream.application.restore_stream_context_uow import (
    RestoreStreamContextUnitOfWork,
    RestoreStreamContextUnitOfWorkFactory,
)
from app.stream.domain.stream_service import StreamService
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyRestoreStreamContextUnitOfWork(SqlAlchemyUnitOfWorkBase, RestoreStreamContextUnitOfWork):
    def __init__(self, session: Session, stream_service: StreamService, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._stream_service = stream_service

    @property
    def stream_service(self) -> StreamService:
        return self._stream_service


class SqlAlchemyRestoreStreamContextUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[RestoreStreamContextUnitOfWork], RestoreStreamContextUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        stream_service_provider: Provider[StreamService],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_service_provider = stream_service_provider

    def _build_uow(self, db: Session, read_only: bool) -> RestoreStreamContextUnitOfWork:
        return SqlAlchemyRestoreStreamContextUnitOfWork(
            session=db,
            stream_service=self._stream_service_provider.get(db),
            read_only=read_only,
        )
