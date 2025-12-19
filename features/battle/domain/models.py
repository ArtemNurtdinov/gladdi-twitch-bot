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

    def has_battles(self) -> bool:
        return self.total_battles > 0

    def get_loss_rate(self) -> float:
        return 100.0 - self.win_rate if self.total_battles > 0 else 0.0

    def __str__(self) -> str:
        return (
            f"UserBattleStats(battles={self.total_battles}, "
            f"wins={self.wins}, win_rate={self.win_rate:.1f}%)"
        )

