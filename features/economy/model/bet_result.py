from typing import Optional
from dataclasses import dataclass
from features.betting.model.rarity_level import RarityLevel


@dataclass
class BetResult:
    success: bool
    balance: int
    bet_cost: Optional[int] = None
    payout: Optional[int] = None
    profit: Optional[int] = None
    result_type: Optional[str] = None
    rarity: Optional[str] = None
    message: Optional[str] = None
    timeout_seconds: Optional[int] = None
    
    @classmethod
    def success_result(cls, bet_cost: int, payout: int, balance: int, result_type: str, 
                      rarity_level: RarityLevel, timeout_seconds: Optional[int] = None) -> 'BetResult':
        profit = payout - bet_cost
        return cls(
            success=True,
            balance=balance,
            bet_cost=bet_cost,
            payout=payout,
            profit=profit,
            result_type=result_type,
            rarity=rarity_level.value,
            timeout_seconds=timeout_seconds
        )
    
    @classmethod
    def failure_result(cls, message: str, required_cost: int) -> 'BetResult':
        return cls(
            success=False,
            balance=0,
            message=message,
            bet_cost=required_cost
        )
    
    def is_win(self) -> bool:
        return self.success and self.payout is not None and self.payout > 0
    
    def is_jackpot(self) -> bool:
        return self.result_type == "jackpot"
    
    def is_partial_match(self) -> bool:
        return self.result_type == "partial"
    
    def is_miss(self) -> bool:
        return self.success and self.result_type == "miss"
    
    def is_consolation_prize(self) -> bool:
        return self.is_miss() and self.payout and self.payout > 0
    
    def should_timeout(self) -> bool:
        return self.timeout_seconds is not None and self.timeout_seconds > 0
    
    def get_timeout_duration(self) -> int:
        return self.timeout_seconds if self.timeout_seconds else 0

    def get_profit_display(self) -> str:
        if not self.success or self.profit is None:
            return ""
        
        if self.is_consolation_prize():
            net_result = self.profit
            if net_result > 0:
                return f"+{net_result}"
            elif net_result < 0:
                return f"{net_result}"
            else:
                return "±0"
        else:
            if self.profit > 0:
                return f"+{self.profit}"
            elif self.profit < 0:
                return f"{self.profit}"
            else:
                return "±0"

    def get_result_emoji(self) -> str:
        if not self.success:
            return "💸"
        
        if self.is_consolation_prize():
            return "🎁"
        elif self.is_jackpot():
            return "🎰"
        elif self.is_partial_match():
            return "✨"
        elif self.is_miss():
            return "💥"
        else:
            return "💰"
    
    def __str__(self) -> str:
        if not self.success:
            return f"BetResult(success=False, message='{self.message}')"
        return f"BetResult(success=True, profit={self.profit}, balance={self.balance})" 