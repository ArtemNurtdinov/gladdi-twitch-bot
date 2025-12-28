from typing import Callable

from sqlalchemy.orm import Session

from app.betting.application.betting_service import BettingService


class BettingServiceProvider:

    def __init__(self, betting_service_factory: Callable[[Session], BettingService]):
        self._betting_service_factory = betting_service_factory

    def get(self, db: Session) -> BettingService:
        return self._betting_service_factory(db)
