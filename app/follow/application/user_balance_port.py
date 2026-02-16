from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BalanceDetail:
    balance: int


class UserBalanceQueryPort(Protocol):
    def get_balance(self, channel_name: str, user_name: str) -> BalanceDetail: ...
