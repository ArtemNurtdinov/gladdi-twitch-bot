from app.battle.domain.model.battle import Battle
from app.battle.infrastructure.db.battle_history import BattleHistory


def map_battle_history(row: BattleHistory) -> Battle:
    return Battle(
        id=row.id,
        channel_name=row.channel_name,
        opponent_1=row.opponent_1,
        opponent_2=row.opponent_2,
        winner=row.winner,
        result_text=row.result_text,
        created_at=row.created_at,
    )
