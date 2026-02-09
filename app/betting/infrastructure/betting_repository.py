from sqlalchemy import select
from sqlalchemy.orm import Session

from app.betting.domain.models import BetRecord, RarityLevel
from app.betting.domain.repo import BettingRepository
from app.betting.infrastructure.db.bet_history import BetHistory
from app.betting.infrastructure.mappers.betting_mapper import map_bet_history


class BettingRepositoryImpl(BettingRepository):
    def __init__(self, db: Session):
        self._db = db

    def save_bet_history(
        self,
        channel_name: str,
        user_name: str,
        slot_result: str,
        result_type: str,
        rarity_level: RarityLevel,
    ):
        bet = BetHistory(
            channel_name=channel_name,
            user_name=user_name,
            slot_result=slot_result,
            result_type=result_type,
            rarity_level=rarity_level,
        )
        self._db.add(bet)

    def get_user_bets(self, channel_name: str, user_name: str) -> list[BetRecord]:
        stmt = select(BetHistory).where(BetHistory.channel_name == channel_name).where(BetHistory.user_name == user_name)
        rows = self._db.execute(stmt).scalars().all()
        return [map_bet_history(row) for row in rows]
