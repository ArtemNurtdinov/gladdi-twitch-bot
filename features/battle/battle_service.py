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

    def get_user_battle_stats(self, user_name: str, channel_name: str) -> UserBattleStats:
        db = SessionLocal()
        try:
            battles = (
                db.query(BattleHistory)
                .filter(((BattleHistory.opponent_1 == user_name) | (BattleHistory.opponent_2 == user_name)) & (BattleHistory.channel_name == channel_name))
                .all()
            )

            if not battles:
                return UserBattleStats(total_battles=0, wins=0, losses=0, win_rate=0.0)

            total_battles = len(battles)
            wins = sum(1 for battle in battles if battle.winner == user_name)
            losses = total_battles - wins
            win_rate = (wins / total_battles) * 100 if total_battles > 0 else 0.0

            return UserBattleStats(total_battles=total_battles, wins=wins, losses=losses, win_rate=win_rate)
        finally:
            db.close()
