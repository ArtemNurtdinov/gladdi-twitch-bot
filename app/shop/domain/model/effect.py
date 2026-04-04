from abc import ABC
from dataclasses import dataclass


@dataclass
class ItemEffect(ABC):
    pass


@dataclass
class DailyBonusMultiplierEffect(ItemEffect):
    multiplier: float


@dataclass
class TimeoutProtectionEffect(ItemEffect):
    pass


@dataclass
class TimeoutReductionEffect(ItemEffect):
    reduction_factor: float


@dataclass
class RollCooldownOverrideEffect(ItemEffect):
    cooldown_seconds: int


@dataclass
class MaxBetIncreaseEffect(ItemEffect):
    max_bet_amount: int
