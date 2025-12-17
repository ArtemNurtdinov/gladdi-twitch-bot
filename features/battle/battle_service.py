from datetime import datetime
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from features.battle.db.battle_history import BattleHistory


class BattleService:

    def save_battle_history(self, db: Session, channel_name: str, opponent_1: str, opponent_2: str, winner: str, result_text: str):
        battle = BattleHistory(channel_name=channel_name, opponent_1=opponent_1, opponent_2=opponent_2, winner=winner, result_text=result_text)
        db.add(battle)

    def get_user_battles(self, db: Session, channel_name: str, user_name: str) -> list[BattleHistory]:
        return db.query(BattleHistory).filter(
            and_(
                or_(
                    BattleHistory.opponent_1 == user_name,
                    BattleHistory.opponent_2 == user_name
                ),
                BattleHistory.channel_name == channel_name
            )
        ).all()

    def get_battles(self, db: Session, channel_name: str, from_time: datetime) -> list[BattleHistory]:
        return db.query(BattleHistory).filter(BattleHistory.channel_name == channel_name).filter(BattleHistory.created_at >= from_time).all()
