from db.base import SessionLocal
from features.battle.db.battle_history import BattleHistory


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
