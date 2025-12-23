from datetime import datetime, timedelta

from app.economy.domain.models import ShopItems, TimeoutProtectionEffect, ShopItemType, TimeoutReductionEffect, RollCooldownOverrideEffect
from app.equipment.domain.models import UserEquipmentItem
from app.equipment.domain.repo import EquipmentRepository


class EquipmentService:

    def __init__(self, repo: EquipmentRepository):
        self._repo = repo

    def get_user_equipment(self, channel_name: str, user_name: str) -> list[UserEquipmentItem]:
        return self._repo.list_user_equipment(channel_name, user_name)

    def calculate_timeout_with_equipment(self, base_timeout_seconds: int, equipment: list[UserEquipmentItem]) -> tuple[int, str]:
        if base_timeout_seconds <= 0:
            return 0, ""

        if not equipment:
            return base_timeout_seconds, ""

        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, TimeoutProtectionEffect):
                    if item.item_type == ShopItemType.MAEL_EXPEDITION:
                        return 0, "⚔️ Маэль перерисовала судьбу и спасла от таймаута! Фоном играет \"Алиииинаааа аииииии\"..."
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

    def calculate_roll_cooldown_seconds(self, default_cooldown_seconds: int, equipment: list[UserEquipmentItem]) -> int:
        min_cooldown = default_cooldown_seconds
        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, RollCooldownOverrideEffect):
                    min_cooldown = min(min_cooldown, effect.cooldown_seconds)
        return min_cooldown

    def equipment_exists(self, channel_name: str, user_name: str, item_type: ShopItemType) -> bool:
        return self._repo.equipment_exists(channel_name, user_name, item_type)

    def add_equipment_to_user(self, channel_name: str, user_name: str, item_type: ShopItemType):
        expires_at = datetime.utcnow() + timedelta(days=30)
        item = UserEquipmentItem(item_type=item_type, shop_item=ShopItems.get_item(item_type), expires_at=expires_at)
        self._repo.add_equipment(channel_name, user_name, item)
