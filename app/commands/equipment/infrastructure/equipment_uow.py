from __future__ import annotations

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.commands.equipment.application.equipment_uow import EquipmentUnitOfWork, EquipmentUnitOfWorkFactory
from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyEquipmentUnitOfWork(SqlAlchemyUnitOfWorkBase, EquipmentUnitOfWork):
    def __init__(
        self,
        session: Session,
        get_user_equipment_use_case: GetUserEquipmentUseCase,
        chat_use_case: ChatUseCase,
        read_only: bool,
    ):
        super().__init__(session=session, read_only=read_only)
        self._get_user_equipment_use_case = get_user_equipment_use_case
        self._chat_use_case = chat_use_case

    @property
    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase:
        return self._get_user_equipment_use_case

    @property
    def chat_use_case(self) -> ChatUseCase:
        return self._chat_use_case


class SqlAlchemyEquipmentUnitOfWorkFactory(SqlAlchemyUnitOfWorkFactory[EquipmentUnitOfWork], EquipmentUnitOfWorkFactory):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        get_user_equipment_use_case_provider: Provider[GetUserEquipmentUseCase],
        chat_use_case_provider: Provider[ChatUseCase],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._get_user_equipment_use_case_provider = get_user_equipment_use_case_provider
        self._chat_use_case_provider = chat_use_case_provider

    def _build_uow(self, db: Session, read_only: bool) -> EquipmentUnitOfWork:
        return SqlAlchemyEquipmentUnitOfWork(
            session=db,
            get_user_equipment_use_case=self._get_user_equipment_use_case_provider.get(db),
            chat_use_case=self._chat_use_case_provider.get(db),
            read_only=read_only,
        )
