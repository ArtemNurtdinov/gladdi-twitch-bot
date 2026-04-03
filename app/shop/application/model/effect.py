from abc import ABC
from dataclasses import dataclass


@dataclass
class ItemEffectDTO(ABC):
    pass


@dataclass
class DailyBonusMultiplierEffectDTO(ItemEffectDTO):
    multiplier: float
    message: str


@dataclass
class MinigamePrizeMultiplierEffectDTO(ItemEffectDTO):
    multiplier: float
    message: str


@dataclass
class TimeoutProtectionEffectDTO(ItemEffectDTO):
    timeout_protect_message: str
    pass


@dataclass
class TimeoutReductionEffectDTO(ItemEffectDTO):
    reduction_factor: float
    timeout_reduct_message: str


@dataclass
class RollCooldownOverrideEffectDTO(ItemEffectDTO):
    cooldown_seconds: int


@dataclass
class MaxBetIncreaseEffectDTO(ItemEffectDTO):
    max_bet_amount: int
