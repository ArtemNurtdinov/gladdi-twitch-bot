from __future__ import annotations

from dataclasses import dataclass

from app.battle.bootstrap import BattleProviders, build_battle_providers
from app.betting.bootstrap import BettingProviders, build_betting_providers
from app.core.logger.domain.logger import Logger
from app.economy.bootstrap import EconomyProviders, build_economy_providers
from app.equipment.bootstrap import EquipmentProviders, build_equipment_providers
from app.minigame.bootstrap import MinigameProviders, build_minigame_providers
from app.viewer.bootstrap import ViewerProviders, build_viewer_providers


@dataclass(frozen=True)
class ProvidersBundle:
    viewer_providers: ViewerProviders
    economy_providers: EconomyProviders
    equipment_providers: EquipmentProviders
    minigame_providers: MinigameProviders
    battle_providers: BattleProviders
    betting_providers: BettingProviders


def build_providers_bundle(logger: Logger) -> ProvidersBundle:
    viewer_providers = build_viewer_providers()
    economy_providers = build_economy_providers()
    equipment_providers = build_equipment_providers()
    minigame_providers = build_minigame_providers(logger=logger)
    battle_providers = build_battle_providers()
    betting_providers = build_betting_providers()

    return ProvidersBundle(
        viewer_providers=viewer_providers,
        economy_providers=economy_providers,
        equipment_providers=equipment_providers,
        minigame_providers=minigame_providers,
        battle_providers=battle_providers,
        betting_providers=betting_providers,
    )
