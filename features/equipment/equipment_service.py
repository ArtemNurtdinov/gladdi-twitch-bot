import logging
from datetime import datetime
from db.database import SessionLocal
from features.equipment.db.user_equipment import UserEquipment
from features.equipment.model.user_equipment_item import UserEquipmentItem
from features.economy.model.shop_items import ShopItems

logger = logging.getLogger(__name__)


class EquipmentService:

    def get_user_equipment(self, channel_name: str, user_name: str) -> list[UserEquipmentItem]:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            equipment = (
                db.query(UserEquipment)
                .filter_by(channel_name=channel_name, user_name=normalized_user_name)
                .filter(UserEquipment.expires_at > datetime.utcnow())
                .all()
            )

            result = []
            for item in equipment:
                shop_item = ShopItems.get_item(item.item_type)
                result.append(UserEquipmentItem(item_type=item.item_type, shop_item=shop_item, expires_at=item.expires_at))

            return result
        except Exception as e:
            logger.error(f"Ошибка при получении экипировки пользователя {user_name}: {e}")
            return []
        finally:
            db.close()
