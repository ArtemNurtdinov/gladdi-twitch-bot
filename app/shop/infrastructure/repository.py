from sqlalchemy import select
from sqlalchemy.orm import Session

from app.shop.domain.model.shop_item import ShopItem, ShopItemCreate
from app.shop.domain.repository import ShopItemRepository
from app.shop.infrastructure.db.model.shop_item import ShopItem as ShopItemORM
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper


class ShopItemRepositoryImpl(ShopItemRepository):
    def __init__(self, db: Session, mapper: ShopItemMapper):
        self._db = db
        self._mapper = mapper

    def get_active_items(self) -> list[ShopItem]:
        stmt = select(ShopItemORM).where(ShopItemORM.is_active)
        orm_items = self._db.execute(stmt).scalars().all()
        return [self._mapper.map_to_domain(item) for item in orm_items]

    def get_active_item_by_name(self, name: str) -> ShopItem | None:
        stmt = select(ShopItemORM).where(ShopItemORM.is_active).where(ShopItemORM.name == name)
        orm_item = self._db.execute(stmt).scalars().first()
        return self._mapper.map_to_domain(orm_item) if orm_item else None

    def create_item(self, shop_item: ShopItemCreate, is_active: bool):
        shop_item_db = self._mapper.map_create_to_db(shop_item, is_active)
        self._db.add(shop_item_db)
        self._db.flush()
        return self._mapper.map_to_domain(shop_item_db)

    def deactivate_item(self, item_id: int) -> None:
        orm_item = self._db.get(ShopItemORM, item_id)
        if orm_item:
            orm_item.is_active = False
