from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shop.domain.model.shop_item import ShopItem, ShopItemCreate, ShopItemPatch
from app.shop.domain.repository import ShopItemRepository
from app.shop.infrastructure.db.model.shop_item import ShopItem as ShopItemORM
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper


class ShopItemRepositoryImpl(ShopItemRepository):
    def __init__(self, db: Session, mapper: ShopItemMapper):
        self._db = db
        self._mapper = mapper

    def get_all_items(self, channel_name: str) -> list[ShopItem]:
        stmt = select(ShopItemORM).where(ShopItemORM.channel_name == channel_name)
        orm_items = self._db.execute(stmt).scalars().all()
        return [self._mapper.map_to_domain(item) for item in orm_items]

    async def get_item_by_id(self, shop_item_id: int) -> ShopItem | None:
        stmt = select(ShopItemORM).where(ShopItemORM.id == shop_item_id)
        orm_item = self._db.execute(stmt).scalars().first()
        return self._mapper.map_to_domain(orm_item) if orm_item else None

    def get_active_items(self) -> list[ShopItem]:
        stmt = select(ShopItemORM).where(ShopItemORM.is_active)
        orm_items = self._db.execute(stmt).scalars().all()
        return [self._mapper.map_to_domain(item) for item in orm_items]

    def get_active_item_by_name(self, name: str) -> ShopItem | None:
        stmt = select(ShopItemORM).where(ShopItemORM.is_active).where(ShopItemORM.name == name)
        orm_item = self._db.execute(stmt).scalars().first()
        return self._mapper.map_to_domain(orm_item) if orm_item else None

    async def create_item(self, shop_item: ShopItemCreate) -> ShopItem:
        shop_item_db = self._mapper.map_create_to_db(shop_item)
        self._db.add(shop_item_db)
        self._db.flush()
        return self._mapper.map_to_domain(shop_item_db)

    def deactivate_item(self, item_id: int) -> None:
        orm_item = self._db.get(ShopItemORM, item_id)
        if orm_item:
            orm_item.is_active = False

    async def delete_item(self, item_id: int) -> None:
        orm_item = self._db.get(ShopItemORM, item_id)
        if orm_item:
            self._db.delete(orm_item)

    async def patch_shop_item(self, shop_item: ShopItemPatch) -> ShopItem | None:
        orm_item: ShopItemORM | None = self._db.get(ShopItemORM, shop_item.id)

        if not orm_item:
            return None

        if shop_item.channel_name is not None:
            orm_item.channel_name = shop_item.channel_name

        if shop_item.name is not None:
            orm_item.name = shop_item.name

        if shop_item.description is not None:
            orm_item.description = shop_item.description

        if shop_item.price is not None:
            orm_item.price = shop_item.price

        if shop_item.emoji is not None:
            orm_item.emoji = shop_item.emoji

        if shop_item.is_active is not None:
            orm_item.is_active = shop_item.is_active

        if shop_item.effects is not None:
            orm_item.effects = [self._mapper.map_effect_to_db(effect) for effect in shop_item.effects]

        self._db.flush()

        return self._mapper.map_to_domain(orm_item)
