from dataclasses import dataclass

from app.battle.application.battle_use_case import BattleUseCase
from app.battle.data.battle_repository import BattleRepositoryImpl
from core.provider import Provider


@dataclass
class BattleProviders:
    battle_use_case_provider: Provider[BattleUseCase]


def build_battle_providers() -> BattleProviders:
    def battle_use_case(db):
        return BattleUseCase(BattleRepositoryImpl(db))

    return BattleProviders(
        battle_use_case_provider=Provider(battle_use_case),
    )
