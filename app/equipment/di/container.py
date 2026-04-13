from sqlalchemy.orm import Session

from app.equipment.application.equipment_use_case_uow import EquipmentUseCaseUnitOfWorkFactory
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.equipment.domain.repo import EquipmentRepository
from app.equipment.infrastructure.equipment_repository import EquipmentRepositoryImpl
from app.equipment.infrastructure.equipment_use_case_uow import SqlAlchemyEquipmentUseCaseUnitOfWorkFactory
from app.equipment.infrastructure.mapper.user_equipment_mapper import UserEquipmentMapper
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper
from core.provider import Provider
from core.types import SessionFactory


class EquipmentContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._shop_item_mapper = ShopItemMapper()
        self._user_equipment_mapper = UserEquipmentMapper(self._shop_item_mapper)
        self._equipment_repository_provider = Provider(self.equipment_repository)

    def equipment_repository(self, session: Session) -> EquipmentRepository:
        return EquipmentRepositoryImpl(session, self._user_equipment_mapper)

    def equipment_use_case_uow_factory(self) -> EquipmentUseCaseUnitOfWorkFactory:
        return SqlAlchemyEquipmentUseCaseUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            equipment_repo_provider=self._equipment_repository_provider,
        )

    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase:
        equipment_use_case_uow_factory = self.equipment_use_case_uow_factory()
        return GetUserEquipmentUseCase(equipment_use_case_uow_factory)
