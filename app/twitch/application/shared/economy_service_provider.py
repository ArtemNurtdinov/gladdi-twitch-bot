from typing import Callable

from sqlalchemy.orm import Session

from app.economy.domain.economy_service import EconomyService


class EconomyServiceProvider:

    def __init__(self, economy_service_factory: Callable[[Session], EconomyService]):
        self.economy_service_factory = economy_service_factory

    def get(self, db: Session) -> EconomyService:
        return self.economy_service_factory(db)
