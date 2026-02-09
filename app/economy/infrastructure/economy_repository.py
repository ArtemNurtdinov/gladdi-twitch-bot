from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.economy.domain.models import BalanceBrief, TransactionData, UserBalanceInfo
from app.economy.domain.repo import EconomyRepository
from app.economy.infrastructure.db.transaction_history import TransactionHistory
from app.economy.infrastructure.db.user_balance import UserBalance


class EconomyRepositoryImpl(EconomyRepository):
    def __init__(self, db: Session):
        self._db = db

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

    def get_balance(self, channel_name: str, user_name: str) -> UserBalanceInfo | None:
        stmt = select(UserBalance).where(UserBalance.channel_name == channel_name).where(UserBalance.user_name == user_name)
        row = self._db.execute(stmt).scalars().first()
        return self._to_info(row) if row else None

    def create_balance(self, channel_name: str, user_name: str, starting_balance: int) -> UserBalanceInfo:
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
        self._db.add(row)
        self._db.flush()
        self._db.refresh(row)
        return self._to_info(row)

    def save_balance(self, balance: UserBalanceInfo) -> UserBalanceInfo:
        row = None
        if balance.id:
            stmt = select(UserBalance).where(UserBalance.id == balance.id)
            row = self._db.execute(stmt).scalars().first()

        if not row:
            row = UserBalance(channel_name=balance.channel_name, user_name=balance.user_name)
            self._db.add(row)

        row.balance = balance.balance
        row.total_earned = balance.total_earned
        row.total_spent = balance.total_spent
        row.last_daily_claim = balance.last_daily_claim
        row.last_bonus_stream_id = balance.last_bonus_stream_id
        row.message_count = balance.message_count
        row.last_activity_reward = balance.last_activity_reward
        row.updated_at = balance.updated_at or datetime.utcnow()

        self._db.flush()
        self._db.refresh(row)
        return self._to_info(row)

    def add_transaction(self, tx: TransactionData) -> None:
        self._db.add(
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

    def get_top_users(self, channel_name: str, limit: int) -> list[BalanceBrief]:
        stmt = select(UserBalance).where(UserBalance.channel_name == channel_name).order_by(UserBalance.balance.desc()).limit(limit)
        rows = self._db.execute(stmt).scalars().all()
        return [BalanceBrief(user_name=r.user_name, balance=r.balance) for r in rows]

    def get_bottom_users(self, channel_name: str, limit: int) -> list[BalanceBrief]:
        stmt = select(UserBalance).where(UserBalance.channel_name == channel_name).order_by(UserBalance.balance.asc()).limit(limit)
        rows = self._db.execute(stmt).scalars().all()
        return [BalanceBrief(user_name=r.user_name, balance=r.balance) for r in rows]
