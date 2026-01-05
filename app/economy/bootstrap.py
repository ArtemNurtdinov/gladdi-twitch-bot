from dataclasses import dataclass

from app.economy.data.economy_repository import EconomyRepositoryImpl
from app.economy.domain.economy_policy import EconomyPolicy
from core.provider import Provider


@dataclass
class EconomyProviders:
    economy_policy_provider: Provider[EconomyPolicy]


def build_economy_providers() -> EconomyProviders:
    def economy_policy(db):
        return EconomyPolicy(EconomyRepositoryImpl(db))

    return EconomyProviders(economy_policy_provider=Provider(economy_policy))
