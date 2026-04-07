from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.platform.command.bonus.application.bonus_uow import BonusUnitOfWork, BonusUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyBonusUnitOfWork(SqlAlchemyUnitOfWorkBase, BonusUnitOfWork):
    def __init__(
        self,
        session: Session,
        stream_repository: StreamRepository,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy: EconomyPolicy,
        chat_use_case: ChatUseCase,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._stream_repository = stream_repository
        self._get_user_equipment_use_case = get_user_equipment_use_case
        self._economy_policy = economy_policy
        self._chat_use_case = chat_use_case

    @property
    def stream_repository(self) -> StreamRepository:
        return self._stream_repository

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase:
        return self._get_user_equipment_use_case

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyBonusUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[BonusUnitOfWork], BonusUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        stream_repository_provider: Provider[StreamRepository],
        get_user_equipment_use_case_provider: Provider[GetUserEquipmentUseCase],
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_repository_provider = stream_repository_provider
        self._get_user_equipment_use_case_provider = get_user_equipment_use_case_provider
        self._economy_policy_provider = economy_policy_provider
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> BonusUnitOfWork:
        return SqlAlchemyBonusUnitOfWork(
            session=db,
            stream_repository=self._stream_repository_provider.get(db),
            get_user_equipment_use_case=self._get_user_equipment_use_case_provider.get(db),
            economy_policy=self._economy_policy_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
