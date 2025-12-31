from typing import Protocol

from app.betting.domain.models import BetRecord, RarityLevel


class BettingRepository(Protocol):
    def save_bet_history(
        self,
        channel_name: str,
        user_name: str,
        slot_result: str,
        result_type: str,
        rarity_level: RarityLevel,
    ): ...

    def get_user_bets(self, channel_name: str, user_name: str) -> list[BetRecord]: ...
