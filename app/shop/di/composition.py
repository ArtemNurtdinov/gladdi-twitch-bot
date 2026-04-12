from fastapi import Depends
from sqlalchemy.orm import Session

from app.shop.application.mapper.effect_mapper import EffectMapper as EffectAppMapper
from app.shop.application.mapper.shop_item_mapper import ShopItemMapper as ShopItemAppMapper
from app.shop.application.usecase.create_shop_item_use_case import CreateShopItemUseCase
from app.shop.application.usecase.delete_shop_item_use_case import DeleteShopItemUseCase
from app.shop.application.usecase.get_all_shop_items_use_case import GetAllShopItemsUseCase
from app.shop.application.usecase.get_shop_item_use_case import GetShopItemUseCase
from app.shop.application.usecase.patch_shop_item_use_case import PatchShopItemUseCase
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper
from app.shop.infrastructure.repository import ShopItemRepositoryImpl
from app.shop.presentation.api.mapper.shop_item_effect_schema_mapper import ShopItemEffectSchemaMapper
from app.shop.presentation.api.mapper.shop_item_schema_mapper import ShopItemSchemaMapper
from core.db import get_db


class ShopContainer:
    def __init__(self, session: Session):
        self._session = session
        self._shop_item_infra_mapper = ShopItemMapper()
        self._shop_item_effect_app_mapper = EffectAppMapper()
        self._shop_item_app_mapper = ShopItemAppMapper(self._shop_item_effect_app_mapper)
        self._shop_item_repository = ShopItemRepositoryImpl(db=self._session, mapper=self._shop_item_infra_mapper)
        self._shop_item_effect_schema_mapper = ShopItemEffectSchemaMapper()
        self.shop_item_schema_mapper = ShopItemSchemaMapper(self._shop_item_effect_schema_mapper)
        self.get_all_use_case = GetAllShopItemsUseCase(self._shop_item_repository, self._shop_item_app_mapper)
        self.create_shop_item_use_case = CreateShopItemUseCase(self._shop_item_repository, self._shop_item_app_mapper)
        self.delete_shop_item_use_case = DeleteShopItemUseCase(self._shop_item_repository)
        self.get_shop_item_use_case = GetShopItemUseCase(self._shop_item_repository, self._shop_item_app_mapper)
        self.patch_shop_item_use_case = PatchShopItemUseCase(self._shop_item_repository, self._shop_item_app_mapper)


def get_shop_container(session: Session = Depends(get_db)) -> ShopContainer:
    return ShopContainer(session)
