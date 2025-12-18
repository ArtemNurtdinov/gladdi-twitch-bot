from typing import Protocol, Generic, TypeVar, Optional

from features.economy.domain.models import UserBalanceInfo, TransactionData, BalanceBrief

DB = TypeVar("DB")


class EconomyRepository(Protocol, Generic[DB]):
    def get_balance(self, db: DB, channel_name: str, user_name: str) -> Optional[UserBalanceInfo]:
        ...

    def create_balance(self, db: DB, channel_name: str, user_name: str, starting_balance: int) -> UserBalanceInfo:
        ...

    def save_balance(self, db: DB, balance: UserBalanceInfo) -> UserBalanceInfo:
        ...

    def add_transaction(self, db: DB, tx: TransactionData) -> None:
        ...

    def get_top_users(self, db: DB, channel_name: str, limit: int) -> list[BalanceBrief]:
        ...

    def get_bottom_users(self, db: DB, channel_name: str, limit: int) -> list[BalanceBrief]:
        ...

