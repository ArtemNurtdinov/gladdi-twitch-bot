from datetime import datetime
from typing import Protocol

from app.battle.domain.model.battle import Battle


class BattleRepository(Protocol):
    def save_battle_history(
        self,
        channel_name: str,
        opponent_1: str,
        opponent_2: str,
        winner: str,
        result_text: str,
    ): ...

    def get_user_battles(self, channel_name: str, user_name: str) -> list[Battle]: ...

    def get_battles(self, channel_name: str, from_time: datetime) -> list[Battle]: ...
