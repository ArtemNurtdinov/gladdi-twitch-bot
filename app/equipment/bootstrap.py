from dataclasses import dataclass

from app.equipment.application.add_equipment_use_case import AddEquipmentUseCase
from app.equipment.application.defense.calculate_timeout_use_case import CalculateTimeoutUseCase
from app.equipment.application.defense.roll_cooldown_use_case import RollCooldownUseCase
from app.equipment.application.equipment_exists_use_case import EquipmentExistsUseCase
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.equipment.data.equipment_repository import EquipmentRepositoryImpl
from app.equipment.infrastructure.equipment_use_case_uow import SqlAlchemyEquipmentUseCaseUnitOfWorkFactory
from core.db import db_ro_session, db_rw_session
from core.provider import Provider, SingletonProvider


@dataclass
class EquipmentProviders:
    get_user_equipment_use_case_provider: Provider[GetUserEquipmentUseCase]
    equipment_exists_use_case_provider: Provider[EquipmentExistsUseCase]
    add_equipment_use_case_provider: Provider[AddEquipmentUseCase]
    roll_cooldown_use_case_provider: SingletonProvider[RollCooldownUseCase]
    calculate_timeout_use_case_provider: SingletonProvider[CalculateTimeoutUseCase]


def build_equipment_providers() -> EquipmentProviders:
    def equipment_repo(db):
        return EquipmentRepositoryImpl(db)

    def get_user_equipment_use_case(db):
        return GetUserEquipmentUseCase(
            unit_of_work_factory=SqlAlchemyEquipmentUseCaseUnitOfWorkFactory(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                equipment_repo_provider=Provider(equipment_repo),
            )
        )

    def equipment_exists_use_case(db):
        return EquipmentExistsUseCase(
            unit_of_work_factory=SqlAlchemyEquipmentUseCaseUnitOfWorkFactory(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                equipment_repo_provider=Provider(equipment_repo),
            )
        )

    def add_equipment_use_case(db):
        return AddEquipmentUseCase(
            unit_of_work_factory=SqlAlchemyEquipmentUseCaseUnitOfWorkFactory(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                equipment_repo_provider=Provider(equipment_repo),
            )
        )

    def roll_cooldown_use_case():
        return RollCooldownUseCase()

    def calculate_timeout_use_case():
        return CalculateTimeoutUseCase()

    return EquipmentProviders(
        get_user_equipment_use_case_provider=Provider(get_user_equipment_use_case),
        equipment_exists_use_case_provider=Provider(equipment_exists_use_case),
        add_equipment_use_case_provider=Provider(add_equipment_use_case),
        roll_cooldown_use_case_provider=SingletonProvider(roll_cooldown_use_case),
        calculate_timeout_use_case_provider=SingletonProvider(calculate_timeout_use_case),
    )
