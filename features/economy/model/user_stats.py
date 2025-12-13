from typing import Dict, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class UserStats:
    balance: int
    total_earned: int
    total_spent: int
    net_profit: int
    last_daily_claim: Optional[datetime]
    can_claim_daily: bool
    created_at: datetime
    transaction_counts: Dict[str, int]
    
    def get_daily_bonuses_claimed(self) -> int:
        return self.transaction_counts.get('daily_bonus', 0)
    
    def get_bet_wins(self) -> int:
        return self.transaction_counts.get('bet_win', 0)
    
    def get_bet_losses(self) -> int:
        return self.transaction_counts.get('bet_loss', 0)
    
    def get_total_bets(self) -> int:
        return self.get_bet_wins() + self.get_bet_losses()
    
    def get_bet_win_rate(self) -> float:
        total_bets = self.get_total_bets()
        if total_bets == 0:
            return 0.0
        return (self.get_bet_wins() / total_bets) * 100
    
    def get_battle_wins(self) -> int:
        return self.transaction_counts.get('battle_win', 0)
    
    def get_battle_participations(self) -> int:
        return self.transaction_counts.get('battle_participation', 0)
    
    def get_battle_win_rate(self) -> float:
        participations = self.get_battle_participations()
        if participations == 0:
            return 0.0
        return (self.get_battle_wins() / participations) * 100
    
    def is_profitable(self) -> bool:
        return self.net_profit > 0
    
    def __str__(self) -> str:
        return f"UserStats(balance={self.balance}, net_profit={self.net_profit})" 