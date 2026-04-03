from abc import ABC
from dataclasses import dataclass


@dataclass
class ItemEffect(ABC):
    pass


@dataclass
class DailyBonusMultiplierEffect(ItemEffect):
    multiplier: float
    message: str


@dataclass
class MinigamePrizeMultiplierEffect(ItemEffect):
    multiplier: float
    message: str


@dataclass
class TimeoutProtectionEffect(ItemEffect):
    timeout_protect_message: str
    pass


@dataclass
class TimeoutReductionEffect(ItemEffect):
    reduction_factor: float
    timeout_reduct_message: str


@dataclass
class RollCooldownOverrideEffect(ItemEffect):
    cooldown_seconds: int


@dataclass
class MaxBetIncreaseEffect(ItemEffect):
    max_bet_amount: int
