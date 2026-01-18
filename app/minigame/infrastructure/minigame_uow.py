from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.minigame.application.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.application.minigame_uow import MinigameUnitOfWork, MinigameUnitOfWorkFactory
from app.stream.domain.stream_service import StreamService
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyMinigameUnitOfWork(SqlAlchemyUnitOfWorkBase, MinigameUnitOfWork):
    def __init__(
        self,
        session: Session,
        economy_policy: EconomyPolicy,
        chat_use_case: ChatUseCase,
        stream_service: StreamService,
        get_used_words_use_case: GetUsedWordsUseCase,
        add_used_words_use_case: AddUsedWordsUseCase,
        conversation_service: ConversationService,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._economy_policy = economy_policy
        self._chat_use_case = chat_use_case
        self._stream_service = stream_service
        self._get_used_words_use_case = get_used_words_use_case
        self._add_used_words_use_case = add_used_words_use_case
        self._conversation_service = conversation_service

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case

    @property
    def stream_service(self) -> StreamService:
        return self._stream_service

    @property
    def get_used_words_use_case(self) -> GetUsedWordsUseCase:
        return self._get_used_words_use_case

    @property
    def add_used_words_use_case(self) -> AddUsedWordsUseCase:
        return self._add_used_words_use_case

    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service


class SqlAlchemyMinigameUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[MinigameUnitOfWork], MinigameUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case_provider: Provider[ChatUseCase],
        stream_service_provider: Provider[StreamService],
        get_used_words_use_case_provider: Provider[GetUsedWordsUseCase],
        add_used_words_use_case_provider: Provider[AddUsedWordsUseCase],
        conversation_service_provider: Provider[ConversationService],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._economy_policy_provider = economy_policy_provider
        self._chat_use_case_provider = chat_use_case_provider
        self._stream_service_provider = stream_service_provider
        self._get_used_words_use_case_provider = get_used_words_use_case_provider
        self._add_used_words_use_case_provider = add_used_words_use_case_provider
        self._conversation_service_provider = conversation_service_provider

    def _build_uow(self, db: Session, read_only: bool) -> MinigameUnitOfWork:
        return SqlAlchemyMinigameUnitOfWork(
            session=db,
            economy_policy=self._economy_policy_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            stream_service=self._stream_service_provider.get(db),
            get_used_words_use_case=self._get_used_words_use_case_provider.get(db),
            add_used_words_use_case=self._add_used_words_use_case_provider.get(db),
            conversation_service=self._conversation_service_provider.get(db),
            read_only=read_only,
        )
