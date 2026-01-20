from dataclasses import dataclass

from app.battle.application.battle_use_case import BattleUseCase
from app.battle.data.battle_repository import BattleRepositoryImpl
from app.battle.infrastructure.battle_use_case_uow import SqlAlchemyBattleUseCaseUnitOfWorkFactory
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


@dataclass
class BattleProviders:
    battle_use_case_provider: Provider[BattleUseCase]


def build_battle_providers() -> BattleProviders:
    def battle_repo(db):
        return BattleRepositoryImpl(db)

    def battle_use_case(db):
        return BattleUseCase(
            unit_of_work_factory=SqlAlchemyBattleUseCaseUnitOfWorkFactory(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                battle_repo_provider=Provider(battle_repo),
            )
        )

    return BattleProviders(
        battle_use_case_provider=Provider(battle_use_case),
    )
