from app.shop.application.model.effect import (
    DailyBonusMultiplierEffectDTO,
    ItemEffectDTO,
    MaxBetIncreaseEffectDTO,
    MinigamePrizeMultiplierEffectDTO,
    RollCooldownOverrideEffectDTO,
    TimeoutProtectionEffectDTO,
    TimeoutReductionEffectDTO,
)
from app.shop.domain.model.effect import (
    DailyBonusMultiplierEffect,
    ItemEffect,
    MaxBetIncreaseEffect,
    MinigamePrizeMultiplierEffect,
    RollCooldownOverrideEffect,
    TimeoutProtectionEffect,
    TimeoutReductionEffect,
)


class EffectMapper:
    def map_effect_to_dto(self, effect: ItemEffect) -> ItemEffectDTO:
        if isinstance(effect, DailyBonusMultiplierEffect):
            return DailyBonusMultiplierEffectDTO(multiplier=effect.multiplier, message=effect.message)

        elif isinstance(effect, MinigamePrizeMultiplierEffect):
            return MinigamePrizeMultiplierEffectDTO(multiplier=effect.multiplier, message=effect.message)

        elif isinstance(effect, TimeoutProtectionEffect):
            return TimeoutProtectionEffectDTO(timeout_protect_message=effect.timeout_protect_message)

        elif isinstance(effect, TimeoutReductionEffect):
            return TimeoutReductionEffectDTO(reduction_factor=effect.reduction_factor, timeout_reduct_message=effect.timeout_reduct_message)

        elif isinstance(effect, RollCooldownOverrideEffect):
            return RollCooldownOverrideEffectDTO(cooldown_seconds=effect.cooldown_seconds)

        elif isinstance(effect, MaxBetIncreaseEffect):
            return MaxBetIncreaseEffectDTO(max_bet_amount=effect.max_bet_amount)

        else:
            raise TypeError(f"Unknown effect type: {type(effect)}")

    def map_effect_to_domain(self, effect_dto: ItemEffectDTO) -> ItemEffect:
        if isinstance(effect_dto, DailyBonusMultiplierEffectDTO):
            return DailyBonusMultiplierEffect(multiplier=effect_dto.multiplier, message=effect_dto.message)

        elif isinstance(effect_dto, MinigamePrizeMultiplierEffectDTO):
            return MinigamePrizeMultiplierEffect(multiplier=effect_dto.multiplier, message=effect_dto.message)

        elif isinstance(effect_dto, TimeoutProtectionEffectDTO):
            return TimeoutProtectionEffect(timeout_protect_message=effect_dto.timeout_protect_message)

        elif isinstance(effect_dto, TimeoutReductionEffectDTO):
            return TimeoutReductionEffect(
                reduction_factor=effect_dto.reduction_factor, timeout_reduct_message=effect_dto.timeout_reduct_message
            )

        elif isinstance(effect_dto, RollCooldownOverrideEffectDTO):
            return RollCooldownOverrideEffect(cooldown_seconds=effect_dto.cooldown_seconds)

        elif isinstance(effect_dto, MaxBetIncreaseEffectDTO):
            return MaxBetIncreaseEffect(max_bet_amount=effect_dto.max_bet_amount)

        else:
            raise TypeError(f"Unknown effect DTO type: {type(effect_dto)}")
