from sqlalchemy.orm import Session

from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase
from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from app.equipment.application.defense.roll_cooldown_use_case import RollCooldownUseCase
from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase
from app.equipment.application.equipment_use_case_uow import EquipmentUseCaseUnitOfWorkFactory
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.equipment.domain.repo import EquipmentRepository
from app.equipment.infrastructure.equipment_repository import EquipmentRepositoryImpl
from app.equipment.infrastructure.equipment_use_case_uow import SqlAlchemyEquipmentUseCaseUnitOfWorkFactory
from app.equipment.infrastructure.mapper.user_equipment_mapper import UserEquipmentMapper
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper
from core.types import SessionFactory


class EquipmentContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._shop_item_mapper = ShopItemMapper()
        self._user_equipment_mapper = UserEquipmentMapper(self._shop_item_mapper)
        self._equipment_repository_factory = SessionScopedFactory(self.equipment_repository)

    def equipment_repository(self, session: Session) -> EquipmentRepository:
        return EquipmentRepositoryImpl(session, self._user_equipment_mapper)

    def equipment_use_case_uow_factory(self) -> EquipmentUseCaseUnitOfWorkFactory:
        return SqlAlchemyEquipmentUseCaseUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            equipment_repository_factory=self._equipment_repository_factory,
        )

    def get_user_equipment_use_case(self) -> GetUserEquipmentUseCase:
        equipment_use_case_uow_factory = self.equipment_use_case_uow_factory()
        return GetUserEquipmentUseCase(equipment_use_case_uow_factory)

    def equipment_exists_use_case(self) -> EquipmentExistsUseCase:
        equipment_use_case_uow_factory = self.equipment_use_case_uow_factory()
        return EquipmentExistsUseCase(equipment_use_case_uow_factory)

    def add_equipment_use_case(self) -> AddEquipmentUseCase:
        equipment_use_case_uow_factory = self.equipment_use_case_uow_factory()
        return AddEquipmentUseCase(equipment_use_case_uow_factory)

    def roll_cooldown_use_case(self) -> RollCooldownUseCase:
        return RollCooldownUseCase()

    def calculate_timeout_use_case(self) -> CalculateTimeoutUseCase:
        return CalculateTimeoutUseCase()
