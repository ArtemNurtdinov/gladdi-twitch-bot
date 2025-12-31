from dataclasses import dataclass

from app.betting.application.betting_service import BettingService
from app.betting.data.betting_repository import BettingRepositoryImpl
from core.provider import Provider


@dataclass
class BettingProviders:
    betting_service_provider: Provider[BettingService]


def build_betting_providers() -> BettingProviders:
    def betting_service(db):
        return BettingService(BettingRepositoryImpl(db))

    return BettingProviders(
        betting_service_provider=Provider(betting_service),
    )
