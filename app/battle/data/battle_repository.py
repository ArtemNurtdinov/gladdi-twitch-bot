from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.battle.data.db.battle_history import BattleHistory
from app.battle.data.mappers.battle_mapper import map_battle_history
from app.battle.domain.models import BattleRecord
from app.battle.domain.repo import BattleRepository


class BattleRepositoryImpl(BattleRepository):
    def __init__(self, db: Session):
        self._db = db

    def save_battle_history(
        self,
        channel_name: str,
        opponent_1: str,
        opponent_2: str,
        winner: str,
        result_text: str,
    ) -> None:
        battle = BattleHistory(
            channel_name=channel_name,
            opponent_1=opponent_1,
            opponent_2=opponent_2,
            winner=winner,
            result_text=result_text,
        )
        self._db.add(battle)

    def get_user_battles(self, channel_name: str, user_name: str) -> list[BattleRecord]:
        stmt = (
            select(BattleHistory)
            .where(BattleHistory.channel_name == channel_name)
            .where(
                or_(
                    BattleHistory.opponent_1 == user_name,
                    BattleHistory.opponent_2 == user_name,
                )
            )
        )
        rows = self._db.execute(stmt).scalars().all()
        return [map_battle_history(row) for row in rows]

    def get_battles(self, channel_name: str, from_time: datetime) -> list[BattleRecord]:
        stmt = (
            select(BattleHistory)
            .where(BattleHistory.channel_name == channel_name)
            .where(BattleHistory.created_at >= from_time)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [map_battle_history(row) for row in rows]
