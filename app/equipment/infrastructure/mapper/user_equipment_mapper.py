from app.equipment.domain.model.user_equipment import UserEquipment
from app.equipment.infrastructure.db.user_equipment import UserEquipment as OrmUserEquipment
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper


class UserEquipmentMapper:
    def __init__(self, shop_item_mapper: ShopItemMapper):
        self._shop_item_mapper = shop_item_mapper

    def map_to_domain(self, user_equipment: OrmUserEquipment) -> UserEquipment:
        shop_item = self._shop_item_mapper.map_to_domain(user_equipment.item)

        return UserEquipment(
            channel_name=user_equipment.channel_name,
            user_name=user_equipment.user_name,
            shop_item_id=user_equipment.shop_item_id,
            shop_item=shop_item,
            expires_at=user_equipment.expires_at,
        )

    def map_to_db(self, user_equipment: UserEquipment) -> OrmUserEquipment:
        return OrmUserEquipment(
            channel_name=user_equipment.channel_name,
            user_name=user_equipment.user_name,
            shop_item_id=user_equipment.shop_item_id,
            expires_at=user_equipment.expires_at,
        )
