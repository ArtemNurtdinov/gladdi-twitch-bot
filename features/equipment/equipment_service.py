import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from features.equipment.db.user_equipment import UserEquipment
from features.equipment.model.user_equipment_item import UserEquipmentItem
from features.economy.model.shop_items import ShopItems, TimeoutProtectionEffect, ShopItemType, TimeoutReductionEffect, RollCooldownOverrideEffect

logger = logging.getLogger(__name__)


class EquipmentService:

    def get_user_equipment(self, db: Session, channel_name: str, user_name: str) -> list[UserEquipmentItem]:
        equipment = db.query(UserEquipment).filter_by(channel_name=channel_name, user_name=user_name).filter(UserEquipment.expires_at > datetime.utcnow()).all()

        result = []
        for item in equipment:
            shop_item = ShopItems.get_item(item.item_type)
            result.append(UserEquipmentItem(item_type=item.item_type, shop_item=shop_item, expires_at=item.expires_at))

        return result

    def calculate_timeout_with_equipment(self, user_name: str, base_timeout_seconds: int, equipment: list[UserEquipmentItem]) -> tuple[int, str]:
        if base_timeout_seconds <= 0:
            return 0, ""

        if not equipment:
            return base_timeout_seconds, ""

        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, TimeoutProtectionEffect):
                    logger.info(f"⚡ ЗАЩИТА ОТ ТАЙМАУТА: {user_name} спасен предметом {item.shop_item.name} (базовый таймаут: {base_timeout_seconds}с)")

                    if item.item_type == ShopItemType.MAEL_EXPEDITION:
                        return 0, "⚔️ Маэль перерисовала судьбу и полностью спасла от таймаута! Фоном играет \"Алиииинаааа аииииии\"..."
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

                    logger.info(f"⚡ СНИЖЕНИЕ ТАЙМАУТА: {user_name} применен эффект от {item.shop_item.name} (множитель: {effect.reduction_factor})")

        if reduction_items:
            reduced_timeout = int(base_timeout_seconds * cumulative_reduction)

            if len(timeout_messages) == 1:
                message = timeout_messages[0]
            else:
                message = f"🔥 СТАК ЗАЩИТЫ! {' + '.join(timeout_messages)}"

            logger.info(f"⚡ ИТОГОВОЕ СНИЖЕНИЕ ТАЙМАУТА: {user_name} (было: {base_timeout_seconds}с, стало: {reduced_timeout}с, общий множитель: {cumulative_reduction:.2f})")
            return reduced_timeout, message

        return base_timeout_seconds, ""

    def calculate_roll_cooldown_seconds(self, default_cooldown_seconds: int, equipment: list[UserEquipmentItem]) -> int:
        min_cooldown = default_cooldown_seconds
        for item in equipment:
            for effect in item.shop_item.effects:
                if isinstance(effect, RollCooldownOverrideEffect):
                    min_cooldown = min(min_cooldown, effect.cooldown_seconds)
        return min_cooldown

    def equipment_exists(self, db: Session, channel_name: str, user_name: str, item_type: ShopItemType) -> bool:
        existing_item = (
            db.query(UserEquipment)
            .filter_by(channel_name=channel_name, user_name=user_name, item_type=item_type)
            .filter(UserEquipment.expires_at > datetime.utcnow())
            .first()
        )
        return existing_item is not None

    def add_equipment_to_user(self, db: Session, channel_name: str, user_name: str, item_type: ShopItemType):
        expires_at = datetime.utcnow() + timedelta(days=30)
        equipment = UserEquipment(channel_name=channel_name, user_name=user_name, item_type=item_type, expires_at=expires_at)
        db.add(equipment)
