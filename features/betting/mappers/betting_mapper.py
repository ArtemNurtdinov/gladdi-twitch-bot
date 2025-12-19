from typing import Optional

from features.betting.data.db.bet_history import BetHistory
from features.betting.domain.models import BetRecord


def map_bet_history(row: Optional[BetHistory]) -> Optional[BetRecord]:
    if row is None:
        return None

    return BetRecord(
        id=row.id,
        channel_name=row.channel_name,
        user_name=row.user_name,
        slot_result=row.slot_result,
        result_type=row.result_type,
        rarity_level=row.rarity_level,
        created_at=row.created_at,
    )