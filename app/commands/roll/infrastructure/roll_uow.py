from __future__ import annotations

from sqlalchemy.orm import Session

from app.betting.application.betting_service import BettingService
from app.chat.application.chat_use_case import ChatUseCase
from app.commands.roll.application.roll_uow import RollUnitOfWork, RollUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyRollUnitOfWork(SqlAlchemyUnitOfWorkBase, RollUnitOfWork):
    def __init__(
        self,
        session: Session,
        economy_policy: EconomyPolicy,
        betting_service: BettingService,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._economy_policy = economy_policy
        self._betting_service = betting_service
        self._get_user_equipment_use_case = get_user_equipment_use_case
        self._chat_use_case = chat_use_case

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def betting_service(self) -> BettingService:
        return self._betting_service

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase:
        return self._get_user_equipment_use_case

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyRollUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[RollUnitOfWork], RollUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        economy_policy_provider: Provider[EconomyPolicy],
        betting_service_provider: Provider[BettingService],
        get_user_equipment_use_case_provider: Provider[GetUserEquipmentUseCase],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._economy_policy_provider = economy_policy_provider
        self._betting_service_provider = betting_service_provider
        self._get_user_equipment_use_case_provider = get_user_equipment_use_case_provider
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> RollUnitOfWork:
        return SqlAlchemyRollUnitOfWork(
            session=db,
            economy_policy=self._economy_policy_provider.get(db),
            betting_service=self._betting_service_provider.get(db),
            get_user_equipment_use_case=self._get_user_equipment_use_case_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
