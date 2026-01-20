from datetime import datetime

from app.battle.application.battle_use_case_uow import BattleUseCaseUnitOfWorkFactory
from app.battle.domain.models import BattleRecord


class BattleUseCase:
    def __init__(self, unit_of_work_factory: BattleUseCaseUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    def save_battle_history(
        self,
        channel_name: str,
        opponent_1: str,
        opponent_2: str,
        winner: str,
        result_text: str,
    ):
        with self._unit_of_work_factory.create() as uow:
            uow.battle_repo.save_battle_history(channel_name, opponent_1, opponent_2, winner, result_text)

    def get_user_battles(self, channel_name: str, user_name: str) -> list[BattleRecord]:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            return uow.battle_repo.get_user_battles(channel_name, user_name)

    def get_battles(self, channel_name: str, from_time: datetime) -> list[BattleRecord]:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            return uow.battle_repo.get_battles(channel_name, from_time)
