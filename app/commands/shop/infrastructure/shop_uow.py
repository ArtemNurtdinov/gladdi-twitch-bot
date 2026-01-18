from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.shop.application.shop_uow import ShopUnitOfWork, ShopUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase
from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyShopUnitOfWork(SqlAlchemyUnitOfWorkBase, ShopUnitOfWork):
    def __init__(
        self,
        session: Session,
        economy_policy: EconomyPolicy,
        add_equipment_use_case: AddEquipmentUseCase,
        equipment_exists_use_case: EquipmentExistsUseCase,
        chat_use_case: ChatUseCase,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._economy_policy = economy_policy
        self._add_equipment_use_case = add_equipment_use_case
        self._equipment_exists_use_case = equipment_exists_use_case
        self._chat_use_case = chat_use_case

    @property
    def economy_policy(self) -> EconomyPolicy:
        return self._economy_policy

    @property
    def add_equipment_use_case(self) -> AddEquipmentUseCase:
        return self._add_equipment_use_case

    @property
    def equipment_exists_use_case(self) -> EquipmentExistsUseCase:
        return self._equipment_exists_use_case

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyShopUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[ShopUnitOfWork], ShopUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        economy_policy_provider: Provider[EconomyPolicy],
        add_equipment_use_case_provider: Provider[AddEquipmentUseCase],
        equipment_exists_use_case_provider: Provider[EquipmentExistsUseCase],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._economy_policy_provider = economy_policy_provider
        self._add_equipment_use_case_provider = add_equipment_use_case_provider
        self._equipment_exists_use_case_provider = equipment_exists_use_case_provider
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> ShopUnitOfWork:
        return SqlAlchemyShopUnitOfWork(
            session=db,
            economy_policy=self._economy_policy_provider.get(db),
            add_equipment_use_case=self._add_equipment_use_case_provider.get(db),
            equipment_exists_use_case=self._equipment_exists_use_case_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
