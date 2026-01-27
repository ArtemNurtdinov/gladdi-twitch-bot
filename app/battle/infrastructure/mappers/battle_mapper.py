from app.battle.domain.models import BattleRecord
from app.battle.infrastructure.db.battle_history import BattleHistory


def map_battle_history(row: BattleHistory | None) -> BattleRecord | None:
    if row is None:
        return None

    return BattleRecord(
        id=row.id,
        channel_name=row.channel_name,
        opponent_1=row.opponent_1,
        opponent_2=row.opponent_2,
        winner=row.winner,
        result_text=row.result_text,
        created_at=row.created_at,
    )
