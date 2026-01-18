from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.bonus.application.bonus_uow import BonusUnitOfWork, BonusUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.stream.domain.stream_service import StreamService
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyBonusUnitOfWork(SqlAlchemyUnitOfWorkBase, BonusUnitOfWork):
    def __init__(
        self,
        session: Session,
        stream_service: StreamService,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        economy_policy: EconomyPolicy,
        chat_use_case: ChatUseCase,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._stream_service = stream_service
        self._get_user_equipment_use_case = get_user_equipment_use_case
        self._economy_policy = economy_policy
        self._chat_use_case = chat_use_case

    @property
    def stream_service(self) -> StreamService:
        return self._stream_service

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
        stream_service_provider: Provider[StreamService],
        get_user_equipment_use_case_provider: Provider[GetUserEquipmentUseCase],
        economy_policy_provider: Provider[EconomyPolicy],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._stream_service_provider = stream_service_provider
        self._get_user_equipment_use_case_provider = get_user_equipment_use_case_provider
        self._economy_policy_provider = economy_policy_provider
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> BonusUnitOfWork:
        return SqlAlchemyBonusUnitOfWork(
            session=db,
            stream_service=self._stream_service_provider.get(db),
            get_user_equipment_use_case=self._get_user_equipment_use_case_provider.get(db),
            economy_policy=self._economy_policy_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
