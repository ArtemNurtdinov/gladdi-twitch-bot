from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.infrastructure.sqlalchemy_uow import SqlAlchemyUnitOfWorkBase, SqlAlchemyUnitOfWorkFactory
from app.equipment.application.equipment_use_case_uow import EquipmentUseCaseUnitOfWork, EquipmentUseCaseUnitOfWorkFactory
from app.equipment.domain.repo import EquipmentRepository
from core.provider import Provider
from core.types import SessionFactory


class SqlAlchemyEquipmentUseCaseUnitOfWork(SqlAlchemyUnitOfWorkBase, EquipmentUseCaseUnitOfWork):
    def __init__(self, session: Session, equipment_repo: EquipmentRepository, read_only: bool):
        super().__init__(session=session, read_only=read_only)
        self._equipment_repo = equipment_repo

    @property
    def equipment_repo(self) -> EquipmentRepository:
        return self._equipment_repo


class SqlAlchemyEquipmentUseCaseUnitOfWorkFactory(
    SqlAlchemyUnitOfWorkFactory[EquipmentUseCaseUnitOfWork], EquipmentUseCaseUnitOfWorkFactory
):
    def __init__(
        self,
        session_factory_rw: SessionFactory,
        session_factory_ro: SessionFactory,
        equipment_repo_provider: Provider[EquipmentRepository],
    ):
        super().__init__(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            builder=self._build_uow,
        )
        self._equipment_repo_provider = equipment_repo_provider

    def _build_uow(self, db: Session, read_only: bool) -> EquipmentUseCaseUnitOfWork:
        return SqlAlchemyEquipmentUseCaseUnitOfWork(
            session=db,
            equipment_repo=self._equipment_repo_provider.get(db),
            read_only=read_only,
        )
