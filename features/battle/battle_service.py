from datetime import datetime

from sqlalchemy import and_, or_

from db.base import SessionLocal
from features.battle.db.battle_history import BattleHistory
from features.battle.model.user_battle_stats import UserBattleStats


class BattleService:

    def save_battle_history(self, channel_name: str, opponent_1: str, opponent_2: str, winner: str, result_text: str):
        db = SessionLocal()
        try:
            battle = BattleHistory(channel_name=channel_name, opponent_1=opponent_1, opponent_2=opponent_2, winner=winner, result_text=result_text)
            db.add(battle)
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Ошибка при сохранении истории битвы: {e}")
        finally:
            db.close()

    def get_user_battles(self, channel_name: str, user_name: str) -> list[BattleHistory]:
        db = SessionLocal()
        try:
            return db.query(BattleHistory).filter(
                and_(
                    or_(
                        BattleHistory.opponent_1 == user_name,
                        BattleHistory.opponent_2 == user_name
                    ),
                    BattleHistory.channel_name == channel_name
                )
            ).all()
        finally:
            db.close()

    def get_battles(self, channel_name: str, from_time: datetime) -> list[BattleHistory]:
        db = SessionLocal()
        try:
            return db.query(BattleHistory).filter(BattleHistory.channel_name == channel_name).filter(BattleHistory.created_at >= from_time).all()
        finally:
            db.close()
