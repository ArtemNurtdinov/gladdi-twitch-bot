from __future__ import annotations

from dataclasses import dataclass

from app.betting.bootstrap import BettingProviders, build_betting_providers


@dataclass(frozen=True)
class ProvidersBundle:
    betting_providers: BettingProviders


def build_providers_bundle() -> ProvidersBundle:
    betting_providers = build_betting_providers()

    return ProvidersBundle(
        betting_providers=betting_providers,
    )
