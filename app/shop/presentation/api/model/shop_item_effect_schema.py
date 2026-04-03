from typing import Literal

from pydantic import BaseModel, Field


class DailyBonusMultiplierEffectSchema(BaseModel):
    type: Literal["daily_bonus_multiplier"] = "daily_bonus_multiplier"
    multiplier: float = Field(..., description="Множитель бонуса", ge=0)
    message: str = Field(..., description="Сообщение эффекта", max_length=255)


class MinigamePrizeMultiplierEffectSchema(BaseModel):
    type: Literal["minigame_prize_multiplier"] = "minigame_prize_multiplier"
    multiplier: float = Field(..., description="Множитель приза", ge=0)
    message: str = Field(..., description="Сообщение эффекта", max_length=255)


class TimeoutProtectionEffectSchema(BaseModel):
    type: Literal["timeout_protection"] = "timeout_protection"
    timeout_protect_message: str = Field(..., description="Сообщение о защите от таймаута", max_length=255)


class TimeoutReductionEffectSchema(BaseModel):
    type: Literal["timeout_reduction"] = "timeout_reduction"
    reduction_factor: float = Field(..., description="Фактор сокращения", ge=0, le=1)
    timeout_reduct_message: str = Field(..., description="Сообщение о сокращении", max_length=255)


class RollCooldownOverrideEffectSchema(BaseModel):
    type: Literal["roll_cooldown_override"] = "roll_cooldown_override"
    cooldown_seconds: int = Field(..., description="Кулдаун в секундах", ge=0)


class MaxBetIncreaseEffectSchema(BaseModel):
    type: Literal["max_bet_increase"] = "max_bet_increase"
    max_bet_amount: int = Field(..., description="Максимальная сумма ставки", ge=0)


ItemEffectSchema = (
    DailyBonusMultiplierEffectSchema
    | MinigamePrizeMultiplierEffectSchema
    | TimeoutProtectionEffectSchema
    | TimeoutReductionEffectSchema
    | RollCooldownOverrideEffectSchema
    | MaxBetIncreaseEffectSchema
)
