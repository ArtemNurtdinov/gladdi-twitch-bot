from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.stream.application.uow.restore_stream_context_uow import (
    RestoreStreamContextUnitOfWork,
    RestoreStreamContextUnitOfWorkFactory,
)
from app.stream.domain.repo import StreamRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyRestoreStreamContextUnitOfWork(SqlAlchemyUnitOfWorkBase, RestoreStreamContextUnitOfWork):
    def __init__(self, session: Session, stream_repository: StreamRepository, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._stream_repository = stream_repository

    @property
    def stream_repository(self) -> StreamRepository:
        return self._stream_repository


class SqlAlchemyRestoreStreamContextUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[RestoreStreamContextUnitOfWork], RestoreStreamContextUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        stream_repository_provider: Provider[StreamRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_repository_provider = stream_repository_provider

    def _build_uow(self, db: Session, read_only: bool) -> RestoreStreamContextUnitOfWork:
        return SqlAlchemyRestoreStreamContextUnitOfWork(
            session=db,
            stream_repository=self._stream_repository_provider.get(db),
            read_only=read_only,
        )
