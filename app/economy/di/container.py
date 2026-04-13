from sqlalchemy.orm import Session

from app.economy.domain.economy_policy import EconomyPolicy
from app.economy.domain.repo import EconomyRepository
from app.economy.infrastructure.economy_repository import EconomyRepositoryImpl
from core.provider import Provider


class EconomyContainer:
    def __init__(self):
        self.economy_policy_provider: Provider[EconomyPolicy] = Provider(self.economy_policy)

    def economy_repository(self, session: Session) -> EconomyRepository:
        return EconomyRepositoryImpl(session)

    def economy_policy(self, session: Session) -> EconomyPolicy:
        economy_repository = self.economy_repository(session)
        return EconomyPolicy(economy_repository)
