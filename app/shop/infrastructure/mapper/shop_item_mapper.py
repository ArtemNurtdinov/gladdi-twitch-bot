from typing import Any

from app.shop.domain.model.effect import (
    DailyBonusMultiplierEffect,
    ItemEffect,
    MaxBetIncreaseEffect,
    MinigamePrizeMultiplierEffect,
    RollCooldownOverrideEffect,
    TimeoutProtectionEffect,
    TimeoutReductionEffect,
)
from app.shop.domain.model.shop_item import ShopItem, ShopItemCreate
from app.shop.infrastructure.db.model.shop_item import ShopItem as ShopItemORM


class ShopItemMapper:
    def map_to_domain(self, shop_item: ShopItemORM) -> ShopItem:
        effects = [self.map_effect_to_domain(effect_dict) for effect_dict in shop_item.effects]

        return ShopItem(
            id=shop_item.id,
            channel_name=shop_item.channel_name,
            name=shop_item.name,
            description=shop_item.description,
            price=shop_item.price,
            emoji=shop_item.emoji,
            effects=effects,
        )

    def map_create_to_db(self, shop_item: ShopItemCreate, is_active: bool) -> ShopItemORM:
        effects_json = [self.map_effect_to_db(effect) for effect in shop_item.effects]
        return ShopItemORM(
            name=shop_item.name,
            channel_name=shop_item.channel_name,
            description=shop_item.description,
            price=shop_item.price,
            emoji=shop_item.emoji,
            effects=effects_json,
            is_active=is_active,
        )

    def map_effect_to_domain(self, effect_dict: dict[str, Any]) -> ItemEffect:
        effect_type = effect_dict.get("type")

        if effect_type == "TimeoutReductionEffect":
            return TimeoutReductionEffect(
                reduction_factor=effect_dict["reduction_factor"], timeout_reduct_message=effect_dict["timeout_reduct_message"]
            )
        elif effect_type == "DailyBonusMultiplierEffect":
            return DailyBonusMultiplierEffect(multiplier=effect_dict["multiplier"], message=effect_dict["message"])
        elif effect_type == "MinigamePrizeMultiplierEffect":
            return MinigamePrizeMultiplierEffect(multiplier=effect_dict["multiplier"], message=effect_dict["message"])
        elif effect_type == "RollCooldownOverrideEffect":
            return RollCooldownOverrideEffect(cooldown_seconds=effect_dict["cooldown_seconds"])
        elif effect_type == "MaxBetIncreaseEffect":
            return MaxBetIncreaseEffect(max_bet_amount=effect_dict["max_bet_amount"])
        elif effect_type == "TimeoutProtectionEffect":
            return TimeoutProtectionEffect(timeout_protect_message=effect_dict["timeout_protect_message"])
        else:
            raise ValueError(f"Unknown effect type: {effect_type}")

    def map_effect_to_db(self, effect: ItemEffect) -> dict[str, Any]:
        if isinstance(effect, TimeoutReductionEffect):
            return {
                "type": "TimeoutReductionEffect",
                "reduction_factor": effect.reduction_factor,
                "timeout_reduct_message": effect.timeout_reduct_message,
            }
        elif isinstance(effect, DailyBonusMultiplierEffect):
            return {"type": "DailyBonusMultiplierEffect", "multiplier": effect.multiplier, "message": effect.message}
        elif isinstance(effect, MinigamePrizeMultiplierEffect):
            return {"type": "MinigamePrizeMultiplierEffect", "multiplier": effect.multiplier, "message": effect.message}
        elif isinstance(effect, RollCooldownOverrideEffect):
            return {"type": "RollCooldownOverrideEffect", "cooldown_seconds": effect.cooldown_seconds}
        elif isinstance(effect, MaxBetIncreaseEffect):
            return {"type": "MaxBetIncreaseEffect", "max_bet_amount": effect.max_bet_amount}
        elif isinstance(effect, TimeoutProtectionEffect):
            return {"type": "TimeoutProtectionEffect", "timeout_protect_message": effect.timeout_protect_message}
        else:
            raise ValueError(f"Unknown effect type: {type(effect).__name__}")
