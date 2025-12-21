from typing import Optional

from app.battle.data.db.battle_history import BattleHistory
from app.battle.domain.models import BattleRecord


def map_battle_history(row: Optional[BattleHistory]) -> Optional[BattleRecord]:
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



