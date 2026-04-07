from sqlalchemy.orm import Session

from app.betting.application.betting_service import BettingService
from app.betting.application.rarity_identifier import RarityIdentifier
from app.betting.domain.repo import BettingRepository
from app.betting.infrastructure.betting_repository import BettingRepositoryImpl
from app.core.common.session.session_scoped_factory import SessionScopedFactory


class BettingContainer:
    def __init__(self):
        self.betting_service_factory = SessionScopedFactory(self.betting_service)

    def betting_repository(self, session: Session) -> BettingRepository:
        return BettingRepositoryImpl(session)

    def betting_service(self, session: Session) -> BettingService:
        betting_repository = self.betting_repository(session)
        rarity_identifier = RarityIdentifier()
        return BettingService(betting_repository, rarity_identifier)
