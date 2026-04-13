from sqlalchemy.orm import Session

from app.battle.application.uow.battle_use_case_uow import BattleUseCaseUnitOfWorkFactory
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.battle.domain.repo import BattleRepository
from app.battle.infrastructure.battle_repository import BattleRepositoryImpl
from app.battle.infrastructure.battle_use_case_uow import SqlAlchemyBattleUseCaseUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


class BattleContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self._battle_repository_provider = Provider(self.battle_repository)

    def battle_repository(self, session: Session) -> BattleRepository:
        return BattleRepositoryImpl(session)

    def battle_use_case_uow_factory(self) -> BattleUseCaseUnitOfWorkFactory:
        return SqlAlchemyBattleUseCaseUnitOfWorkFactory(
            session_factory_rw=self._session_factory_rw,
            session_factory_ro=self._session_factory_ro,
            battle_repo_provider=self._battle_repository_provider,
        )

    def battle_use_case(self) -> BattleUseCase:
        battle_use_case_uow_factory = self.battle_use_case_uow_factory()
        return BattleUseCase(battle_use_case_uow_factory)
