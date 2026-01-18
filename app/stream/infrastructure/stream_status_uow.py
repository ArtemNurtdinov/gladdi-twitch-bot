from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.battle.application.battle_use_case import BattleUseCase
from app.chat.application.chat_use_case import ChatUseCase
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.stream.application.start_new_stream_use_case import StartNewStreamUseCase
from app.stream.application.stream_status_uow import StreamStatusUnitOfWork, StreamStatusUnitOfWorkFactory
from app.stream.domain.stream_service import StreamService
from app.viewer.domain.viewer_session_service import ViewerTimeService
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyStreamStatusUnitOfWork(SqlAlchemyUnitOfWorkBase, StreamStatusUnitOfWork):
    def __init__(
        self,
        session: Session,
        stream_service: StreamService,
        start_stream_use_case: StartNewStreamUseCase,
        viewer_service: ViewerTimeService,
        battle_use_case: BattleUseCase,
        economy_policy: EconomyPolicy,
        chat_use_case: ChatUseCase,
        conversation_service: ConversationService,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._stream_service = stream_service
        self._start_stream_use_case = start_stream_use_case
        self._viewer_service = viewer_service
        self._battle_use_case = battle_use_case
        self._economy_policy = economy_policy
        self._chat_use_case = chat_use_case
        self._conversation_service = conversation_service

    @property
    def stream_service(self) -> StreamService:
        return self._stream_service

    @property
    def start_stream_use_case(self) -> StartNewStreamUseCase:
        return self._start_stream_use_case

    @property
    def viewer_service(self) -> ViewerTimeService:
        return self._viewer_service

    @property
    def battle_use_case(self) -> BattleUseCase:
        return self._battle_use_case

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service


class SqlAlchemyStreamStatusUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[StreamStatusUnitOfWork], StreamStatusUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        stream_service_provider: Provider[StreamService],
        start_stream_use_case_provider: Provider[StartNewStreamUseCase],
        viewer_service_provider: Provider[ViewerTimeService],
        battle_use_case_provider: Provider[BattleUseCase],
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case_provider: Provider[ChatUseCase],
        conversation_service_provider: Provider[ConversationService],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_service_provider = stream_service_provider
        self._start_stream_use_case_provider = start_stream_use_case_provider
        self._viewer_service_provider = viewer_service_provider
        self._battle_use_case_provider = battle_use_case_provider
        self._economy_policy_provider = economy_policy_provider
        self._chat_use_case_provider = chat_use_case_provider
        self._conversation_service_provider = conversation_service_provider

    def _build_uow(self, db: Session, read_only: bool) -> StreamStatusUnitOfWork:
        return SqlAlchemyStreamStatusUnitOfWork(
            session=db,
            stream_service=self._stream_service_provider.get(db),
            start_stream_use_case=self._start_stream_use_case_provider.get(db),
            viewer_service=self._viewer_service_provider.get(db),
            battle_use_case=self._battle_use_case_provider.get(db),
            economy_policy=self._economy_policy_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            conversation_service=self._conversation_service_provider.get(db),
            read_only=read_only,
        )
