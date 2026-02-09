from app.equipment.domain.models import UserEquipmentItem
from app.shop.domain.models import RollCooldownOverrideEffect


class RollCooldownUseCase:
    def calc_seconds(self, default_cooldown_seconds: int, equipment: list[UserEquipmentItem]) -> int:
        min_cooldown = default_cooldown_seconds
        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, RollCooldownOverrideEffect):
                    min_cooldown = min(min_cooldown, effect.cooldown_seconds)
        return min_cooldown
