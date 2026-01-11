from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StatsDTO:
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime


@dataclass(frozen=True)
class UserBetStats:
    total_bets: int
    jackpots: int
    jackpot_rate: float | int
