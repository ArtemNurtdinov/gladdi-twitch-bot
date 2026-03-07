from dataclasses import dataclass

from app.betting.application.betting_service import BettingService
from app.betting.application.rarity_identifier import RarityIdentifier
from app.betting.infrastructure.betting_repository import BettingRepositoryImpl
from core.provider import Provider


@dataclass
class BettingProviders:
    betting_service_provider: Provider[BettingService]


def build_betting_providers() -> BettingProviders:
    def betting_service(db):
        return BettingService(BettingRepositoryImpl(db), rarity_identifier=RarityIdentifier())

    return BettingProviders(
        betting_service_provider=Provider(betting_service),
    )
