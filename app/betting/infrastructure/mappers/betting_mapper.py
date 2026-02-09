from app.betting.domain.models import BetRecord
from app.betting.infrastructure.db.bet_history import BetHistory


def map_bet_history(row: BetHistory | None) -> BetRecord | None:
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
