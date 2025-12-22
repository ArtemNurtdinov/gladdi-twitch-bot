from typing import Protocol, Optional

from app.economy.domain.models import UserBalanceInfo, TransactionData, BalanceBrief

class EconomyRepository(Protocol):

    def get_balance(self, channel_name: str, user_name: str) -> Optional[UserBalanceInfo]:
        ...

    def create_balance(self, channel_name: str, user_name: str, starting_balance: int) -> UserBalanceInfo:
        ...

    def save_balance(self, balance: UserBalanceInfo) -> UserBalanceInfo:
        ...

    def add_transaction(self, tx: TransactionData) -> None:
        ...

    def get_top_users(self, channel_name: str, limit: int) -> list[BalanceBrief]:
        ...

    def get_bottom_users(self, channel_name: str, limit: int) -> list[BalanceBrief]:
        ...

