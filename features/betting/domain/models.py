from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


@dataclass
class BetRecord:
    id: int
    channel_name: str
    user_name: str
    slot_result: str
    result_type: str
    rarity_level: "RarityLevel"
    created_at: datetime


class RarityLevel(Enum):
    COMMON = "COMMON"
    UNCOMMON = "UNCOMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"
    MYTHICAL = "MYTHICAL"


class EmojiConfig:
    EMOJI_SYSTEM = {
        'artemn3STUL': {'rank': 1, 'weight': 40, 'rarity': RarityLevel.COMMON},
        'LUL': {'rank': 2, 'weight': 30, 'rarity': RarityLevel.UNCOMMON},
        'artemn3BOSS': {'rank': 3, 'weight': 20, 'rarity': RarityLevel.RARE},
        'artemn3Facepalm2': {'rank': 4, 'weight': 7, 'rarity': RarityLevel.EPIC},
        'artemn3Chair': {'rank': 5, 'weight': 3, 'rarity': RarityLevel.LEGENDARY},
        'DinoDance': {'rank': 6, 'weight': 0.0001, 'rarity': RarityLevel.MYTHICAL}
    }

    @classmethod
    def get_emoji_rarity(cls, emoji_name: str) -> RarityLevel:
        return cls.EMOJI_SYSTEM.get(emoji_name, {}).get('rarity', RarityLevel.COMMON)

    @classmethod
    def get_emoji_weight(cls, emoji_name: str) -> float:
        return cls.EMOJI_SYSTEM.get(emoji_name, {}).get('weight', 1.0)

    @classmethod
    def get_emojis_list(cls) -> list[str]:
        return list(cls.EMOJI_SYSTEM.keys())

    @classmethod
    def get_weights_list(cls) -> list[float]:
        return [cls.EMOJI_SYSTEM[emoji]['weight'] for emoji in cls.get_emojis_list()]

    @classmethod
    def parse_slot_result(cls, slot_result: str) -> list[str]:
        return [emoji.strip() for emoji in slot_result.split('|')]

    @classmethod
    def format_slot_result(cls, emojis: list[str]) -> str:
        return ' | '.join(emojis)

    @classmethod
    def get_emoji_rarities_dict(cls) -> dict[str, RarityLevel]:
        return {emoji: data['rarity'] for emoji, data in cls.EMOJI_SYSTEM.items()}


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
    def success_result(cls, bet_cost: int, payout: int, balance: int, result_type: str, rarity_level: RarityLevel, timeout_seconds: Optional[int] = None) -> 'BetResult':
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
        return cls(success=False, balance=0, message=message, bet_cost=required_cost)

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
