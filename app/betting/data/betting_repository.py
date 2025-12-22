from sqlalchemy.orm import Session

from app.betting.data.db.bet_history import BetHistory
from app.betting.domain.models import BetRecord, RarityLevel
from app.betting.domain.repo import BettingRepository
from app.betting.data.mappers.betting_mapper import map_bet_history


class BettingRepositoryImpl(BettingRepository[Session]):
    def save_bet_history(
        self,
        db: Session,
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
        db.add(bet)

    def get_user_bets(self, db: Session, channel_name: str, user_name: str) -> list[BetRecord]:
        rows = (
            db.query(BetHistory)
            .filter(BetHistory.user_name == user_name)
            .filter(BetHistory.channel_name == channel_name)
            .all()
        )
        return [map_bet_history(row) for row in rows]



