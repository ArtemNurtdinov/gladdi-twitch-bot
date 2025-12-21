from typing import Generic, Protocol, TypeVar

from app.betting.domain.models import BetRecord, RarityLevel

DB = TypeVar("DB")


class BettingRepository(Protocol, Generic[DB]):
    def save_bet_history(
        self,
        db: DB,
        channel_name: str,
        user_name: str,
        slot_result: str,
        result_type: str,
        rarity_level: RarityLevel,
    ):
        ...

    def get_user_bets(self, db: DB, channel_name: str, user_name: str) -> list[BetRecord]:
        ...



