from app.equipment.domain.models import UserEquipmentItem
from app.shop.domain.model.effect import TimeoutProtectionEffect, TimeoutReductionEffect


class CalculateTimeoutUseCase:
    def calculate_timeout_with_equipment(self, base_timeout_seconds: int, equipment: list[UserEquipmentItem]) -> tuple[int, str]:
        if base_timeout_seconds <= 0:
            return 0, ""

        if not equipment:
            return base_timeout_seconds, ""

        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, TimeoutProtectionEffect):
                    return 0, effect.timeout_protect_message

        reduction_items = []
        cumulative_reduction = 1.0
        timeout_messages = []

        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, TimeoutReductionEffect):
                    reduction_items.append(item)
                    cumulative_reduction *= effect.reduction_factor
                    timeout_messages.append(effect.timeout_reduct_message)

        if reduction_items:
            reduced_timeout = int(base_timeout_seconds * cumulative_reduction)

            if len(timeout_messages) == 1:
                message = timeout_messages[0]
            else:
                message = f"🔥 СТАК ЗАЩИТЫ! {' + '.join(timeout_messages)}"
            return reduced_timeout, message

        return base_timeout_seconds, ""
