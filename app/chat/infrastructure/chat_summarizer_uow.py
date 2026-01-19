from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.chat_summarizer_uow import ChatSummarizerUnitOfWork, ChatSummarizerUnitOfWorkFactory
from app.chat.application.chat_use_case import ChatUseCase
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.stream.domain.stream_service import StreamService
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyChatSummarizerUnitOfWork(SqlAlchemyUnitOfWorkBase, ChatSummarizerUnitOfWork):
    def __init__(self, session: Session, stream_service: StreamService, chat_use_case: ChatUseCase, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._stream_service = stream_service
        self._chat_use_case = chat_use_case

    @property
    def stream_service(self) -> StreamService:
        return self._stream_service

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyChatSummarizerUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[ChatSummarizerUnitOfWork], ChatSummarizerUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        stream_service_provider: Provider[StreamService],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_service_provider = stream_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> ChatSummarizerUnitOfWork:
        return SqlAlchemyChatSummarizerUnitOfWork(
            session=db,
            stream_service=self._stream_service_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
