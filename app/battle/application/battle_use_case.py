from datetime import datetime

from app.battle.domain.models import BattleRecord
from app.battle.domain.repo import BattleRepository


class BattleUseCase:

    def __init__(self, repo: BattleRepository):
        self._repo = repo

    def save_battle_history(
        self,
        channel_name: str,
        opponent_1: str,
        opponent_2: str,
        winner: str,
        result_text: str,
    ):
        self._repo.save_battle_history(channel_name, opponent_1, opponent_2, winner, result_text)

    def get_user_battles(self, channel_name: str, user_name: str) -> list[BattleRecord]:
        return self._repo.get_user_battles(channel_name, user_name)

    def get_battles(self, channel_name: str, from_time: datetime) -> list[BattleRecord]:
        return self._repo.get_battles(channel_name, from_time)