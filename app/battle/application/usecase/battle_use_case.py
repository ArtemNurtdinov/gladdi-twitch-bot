from datetime import datetime

from app.battle.application.uow.battle_use_case_uow import BattleUseCaseUnitOfWorkFactory
from app.battle.domain.model.battle import Battle


class BattleUseCase:
    def __init__(self, battle_uow: BattleUseCaseUnitOfWorkFactory):
        self._battle_uow = battle_uow

    def save_battle_history(
        self,
        channel_name: str,
        opponent_1: str,
        opponent_2: str,
        winner: str,
        result_text: str,
    ):
        with self._battle_uow.create() as uow:
            uow.battle_repo.save_battle_history(channel_name, opponent_1, opponent_2, winner, result_text)

    def get_user_battles(self, channel_name: str, user_name: str) -> list[Battle]:
        with self._battle_uow.create(read_only=True) as uow:
            return uow.battle_repo.get_user_battles(channel_name, user_name)

    def get_battles(self, channel_name: str, from_time: datetime) -> list[Battle]:
        with self._battle_uow.create(read_only=True) as uow:
            return uow.battle_repo.get_battles(channel_name, from_time)
