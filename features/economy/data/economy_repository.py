from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from features.economy.db.user_balance import UserBalance
from features.economy.db.transaction_history import TransactionHistory, TransactionType
from features.economy.domain.models import UserBalanceInfo, TransactionData, BalanceBrief
from features.economy.domain.repo import EconomyRepository


class EconomyRepositoryImpl(EconomyRepository[Session]):
    def _to_info(self, row: UserBalance) -> UserBalanceInfo:
        return UserBalanceInfo(
            id=row.id,
            channel_name=row.channel_name,
            user_name=row.user_name,
            balance=row.balance,
            total_earned=row.total_earned,
            total_spent=row.total_spent,
            last_daily_claim=row.last_daily_claim,
            last_bonus_stream_id=row.last_bonus_stream_id,
            message_count=row.message_count,
            last_activity_reward=row.last_activity_reward,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def get_balance(self, db: Session, channel_name: str, user_name: str) -> Optional[UserBalanceInfo]:
        row = db.query(UserBalance).filter_by(channel_name=channel_name, user_name=user_name).first()
        return self._to_info(row) if row else None

    def create_balance(self, db: Session, channel_name: str, user_name: str, starting_balance: int) -> UserBalanceInfo:
        row = UserBalance(
            channel_name=channel_name,
            user_name=user_name,
            balance=starting_balance,
            total_earned=starting_balance,
            total_spent=0,
            message_count=0,
            last_daily_claim=None,
            last_bonus_stream_id=None,
            last_activity_reward=None,
        )
        db.add(row)
        db.flush()
        db.refresh(row)
        return self._to_info(row)

    def save_balance(self, db: Session, balance: UserBalanceInfo) -> UserBalanceInfo:
        if balance.id:
            row = db.query(UserBalance).filter_by(id=balance.id).first()
        else:
            row = None

        if not row:
            row = UserBalance(
                channel_name=balance.channel_name,
                user_name=balance.user_name,
            )
            db.add(row)

        row.balance = balance.balance
        row.total_earned = balance.total_earned
        row.total_spent = balance.total_spent
        row.last_daily_claim = balance.last_daily_claim
        row.last_bonus_stream_id = balance.last_bonus_stream_id
        row.message_count = balance.message_count
        row.last_activity_reward = balance.last_activity_reward
        row.updated_at = balance.updated_at or datetime.utcnow()

        db.flush()
        db.refresh(row)
        return self._to_info(row)

    def add_transaction(self, db: Session, tx: TransactionData) -> None:
        db.add(
            TransactionHistory(
                channel_name=tx.channel_name,
                user_name=tx.user_name,
                transaction_type=tx.transaction_type,
                amount=tx.amount,
                balance_before=tx.balance_before,
                balance_after=tx.balance_after,
                description=tx.description,
                created_at=tx.created_at,
            )
        )

    def get_top_users(self, db: Session, channel_name: str, limit: int) -> list[BalanceBrief]:
        rows = (
            db.query(UserBalance)
            .filter_by(channel_name=channel_name)
            .order_by(UserBalance.balance.desc())
            .limit(limit)
            .all()
        )
        return [BalanceBrief(user_name=r.user_name, balance=r.balance) for r in rows]

    def get_bottom_users(self, db: Session, channel_name: str, limit: int) -> list[BalanceBrief]:
        rows = (
            db.query(UserBalance)
            .filter_by(channel_name=channel_name)
            .order_by(UserBalance.balance.asc())
            .limit(limit)
            .all()
        )
        return [BalanceBrief(user_name=r.user_name, balance=r.balance) for r in rows]

