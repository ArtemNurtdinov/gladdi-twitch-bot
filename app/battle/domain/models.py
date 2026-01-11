from dataclasses import dataclass
from datetime import datetime


@dataclass
class BattleRecord:
    id: int
    channel_name: str
    opponent_1: str
    opponent_2: str
    winner: str
    result_text: str
    created_at: datetime


@dataclass
class UserBattleStats:
    total_battles: int
    wins: int
    losses: int
    win_rate: float
