from app.shop.application.model.effect import (
    DailyBonusMultiplierEffectDTO,
    ItemEffectDTO,
    MaxBetIncreaseEffectDTO,
    MinigamePrizeMultiplierEffectDTO,
    RollCooldownOverrideEffectDTO,
    TimeoutProtectionEffectDTO,
    TimeoutReductionEffectDTO,
)
from app.shop.presentation.api.model.shop_item_effect_schema import (
    DailyBonusMultiplierEffectSchema,
    ItemEffectSchema,
    MaxBetIncreaseEffectSchema,
    MinigamePrizeMultiplierEffectSchema,
    RollCooldownOverrideEffectSchema,
    TimeoutProtectionEffectSchema,
    TimeoutReductionEffectSchema,
)


class ShopItemEffectSchemaMapper:
    def map_dto_to_schema(self, effect: ItemEffectDTO) -> ItemEffectSchema:
        if isinstance(effect, DailyBonusMultiplierEffectDTO):
            return DailyBonusMultiplierEffectSchema(multiplier=effect.multiplier, message=effect.message)
        elif isinstance(effect, MinigamePrizeMultiplierEffectDTO):
            return MinigamePrizeMultiplierEffectSchema(multiplier=effect.multiplier, message=effect.message)
        elif isinstance(effect, TimeoutProtectionEffectDTO):
            return TimeoutProtectionEffectSchema(timeout_protect_message=effect.timeout_protect_message)
        elif isinstance(effect, TimeoutReductionEffectDTO):
            return TimeoutReductionEffectSchema(
                reduction_factor=effect.reduction_factor, timeout_reduct_message=effect.timeout_reduct_message
            )
        elif isinstance(effect, RollCooldownOverrideEffectDTO):
            return RollCooldownOverrideEffectSchema(cooldown_seconds=effect.cooldown_seconds)
        elif isinstance(effect, MaxBetIncreaseEffectDTO):
            return MaxBetIncreaseEffectSchema(max_bet_amount=effect.max_bet_amount)
        raise TypeError(f"Unknown effect type: {type(effect)}")
