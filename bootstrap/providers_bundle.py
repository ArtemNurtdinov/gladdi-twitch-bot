from __future__ import annotations

from dataclasses import dataclass

from app.battle.bootstrap import BattleProviders, build_battle_providers
from app.betting.bootstrap import BettingProviders, build_betting_providers


@dataclass(frozen=True)
class ProvidersBundle:
    battle_providers: BattleProviders
    betting_providers: BettingProviders


def build_providers_bundle() -> ProvidersBundle:
    battle_providers = build_battle_providers()
    betting_providers = build_betting_providers()

    return ProvidersBundle(
        battle_providers=battle_providers,
        betting_providers=betting_providers,
    )
