from app.equipment.domain.models import UserEquipmentItem
from app.shop.domain.model.effect import TimeoutProtectionEffect, TimeoutReductionEffect
from app.shop.domain.model.type import ShopItemType


class CalculateTimeoutUseCase:
    def calculate_timeout_with_equipment(self, base_timeout_seconds: int, equipment: list[UserEquipmentItem]) -> tuple[int, str]:
        if base_timeout_seconds <= 0:
            return 0, ""

        if not equipment:
            return base_timeout_seconds, ""

        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, TimeoutProtectionEffect):
                    if item.item_type == ShopItemType.MAEL_EXPEDITION:
                        return 0, '⚔️ Маэль перерисовала судьбу и спасла от таймаута! Фоном играет "Алиииинаааа аииииии"...'
                    elif item.item_type == ShopItemType.COMMUNIST_PARTY:
                        return 0, "☭ Партия коммунистов защитила товарища! Единство спасло от таймаута!"
                    elif item.item_type == ShopItemType.GAMBLER_AMULET:
                        return 0, "🎰 Амулет лудомана защитил от таймаута!"
                    else:
                        return 0, f"{item.shop_item.emoji} {item.shop_item.name} спас от таймаута!"

        reduction_items = []
        cumulative_reduction = 1.0
        timeout_messages = []

        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, TimeoutReductionEffect):
                    reduction_items.append(item)
                    cumulative_reduction *= effect.reduction_factor

                    if item.item_type == ShopItemType.CHAIR:
                        timeout_messages.append("🪑 Стул обеспечил надёжную опору и снизил таймаут!")
                    elif item.item_type == ShopItemType.BONFIRE:
                        timeout_messages.append("🔥 Костёр согрел душу и стал чекпоинтом, снизив таймаут!")
                    else:
                        timeout_messages.append(f"{item.shop_item.emoji} {item.shop_item.name} снизил таймаут!")

        if reduction_items:
            reduced_timeout = int(base_timeout_seconds * cumulative_reduction)

            if len(timeout_messages) == 1:
                message = timeout_messages[0]
            else:
                message = f"🔥 СТАК ЗАЩИТЫ! {' + '.join(timeout_messages)}"
            return reduced_timeout, message

        return base_timeout_seconds, ""
