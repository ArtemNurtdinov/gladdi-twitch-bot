from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True)
class ItemEffectDTO(ABC):
    pass


@dataclass(frozen=True)
class DailyBonusMultiplierEffectDTO(ItemEffectDTO):
    multiplier: float
    message: str


@dataclass(frozen=True)
class MinigamePrizeMultiplierEffectDTO(ItemEffectDTO):
    multiplier: float
    message: str


@dataclass(frozen=True)
class TimeoutProtectionEffectDTO(ItemEffectDTO):
    timeout_protect_message: str
    pass


@dataclass(frozen=True)
class TimeoutReductionEffectDTO(ItemEffectDTO):
    reduction_factor: float
    timeout_reduct_message: str


@dataclass(frozen=True)
class RollCooldownOverrideEffectDTO(ItemEffectDTO):
    cooldown_seconds: int


@dataclass(frozen=True)
class MaxBetIncreaseEffectDTO(ItemEffectDTO):
    max_bet_amount: int
