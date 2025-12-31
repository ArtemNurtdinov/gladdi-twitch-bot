from dataclasses import dataclass

from app.economy.data.economy_repository import EconomyRepositoryImpl
from app.economy.domain.economy_service import EconomyService
from core.provider import Provider


@dataclass
class EconomyProviders:
    economy_service_provider: Provider[EconomyService]


def build_economy_providers() -> EconomyProviders:
    def economy_service(db):
        return EconomyService(EconomyRepositoryImpl(db))

    return EconomyProviders(economy_service_provider=Provider(economy_service))
