from dataclasses import dataclass


@dataclass
class UserBattleStats:
    total_battles: int
    wins: int
    losses: int
    win_rate: float
