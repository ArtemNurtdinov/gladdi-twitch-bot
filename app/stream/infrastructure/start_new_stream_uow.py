from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.stream.application.start_new_stream_uow import StartNewStreamUnitOfWork, StartNewStreamUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyStartNewStreamUnitOfWork(SqlAlchemyUnitOfWorkBase, StartNewStreamUnitOfWork):
    def __init__(self, session: Session, stream_repo: StreamRepository, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._stream_repo = stream_repo

    @property
    def stream_repo(self) -> StreamRepository:
        return self._stream_repo


class SqlAlchemyStartNewStreamUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[StartNewStreamUnitOfWork], StartNewStreamUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        stream_repo_provider: Provider[StreamRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_repo_provider = stream_repo_provider

    def _build_uow(self, db: Session, read_only: bool) -> StartNewStreamUnitOfWork:
        return SqlAlchemyStartNewStreamUnitOfWork(
            session=db,
            stream_repo=self._stream_repo_provider.get(db),
            read_only=read_only,
        )
