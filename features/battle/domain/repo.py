from datetime import datetime
from typing import Generic, Protocol, TypeVar

from features.battle.domain.models import BattleRecord

DB = TypeVar("DB")


class BattleRepository(Protocol, Generic[DB]):
    def save_battle_history(
        self,
        db: DB,
        channel_name: str,
        opponent_1: str,
        opponent_2: str,
        winner: str,
        result_text: str,
    ) -> None:
        ...

    def get_user_battles(self, db: DB, channel_name: str, user_name: str) -> list[BattleRecord]:
        ...

    def get_battles(self, db: DB, channel_name: str, from_time: datetime) -> list[BattleRecord]:
        ...

