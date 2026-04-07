from sqlalchemy.orm import Session

from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.shop.application.mapper.effect_mapper import EffectMapper as EffectAppMapper
from app.shop.application.mapper.shop_item_mapper import ShopItemMapper as ShopItemAppMapper
from app.shop.application.usecase.create_shop_item_use_case import CreateShopItemUseCase
from app.shop.application.usecase.delete_shop_item_use_case import DeleteShopItemUseCase
from app.shop.application.usecase.get_all_shop_items_use_case import GetAllShopItemsUseCase
from app.shop.application.usecase.get_shop_item_use_case import GetShopItemUseCase
from app.shop.application.usecase.patch_shop_item_use_case import PatchShopItemUseCase
from app.shop.domain.repository import ShopItemRepository
from app.shop.infrastructure.mapper.shop_item_mapper import ShopItemMapper
from app.shop.infrastructure.repository import ShopItemRepositoryImpl
from app.shop.presentation.api.mapper.shop_item_effect_schema_mapper import ShopItemEffectSchemaMapper
from app.shop.presentation.api.mapper.shop_item_schema_mapper import ShopItemSchemaMapper


class ShopContainer:
    def __init__(self):
        self._shop_item_infra_mapper = ShopItemMapper()
        self._shop_item_effect_app_mapper = EffectAppMapper()
        self._shop_item_app_mapper = ShopItemAppMapper(self._shop_item_effect_app_mapper)
        self._shop_item_effect_schema_mapper = ShopItemEffectSchemaMapper()
        self.shop_item_schema_mapper = ShopItemSchemaMapper(self._shop_item_effect_schema_mapper)
        self.shop_item_repository_factory = SessionScopedFactory(self.shop_item_repository)

    def shop_item_repository(self, session: Session) -> ShopItemRepository:
        return ShopItemRepositoryImpl(session, self._shop_item_infra_mapper)

    def get_all_use_case(self, session: Session) -> GetAllShopItemsUseCase:
        repository = self.shop_item_repository(session)
        return GetAllShopItemsUseCase(repository, self._shop_item_app_mapper)

    def create_shop_item_use_case(self, session: Session) -> CreateShopItemUseCase:
        repository = self.shop_item_repository(session)
        return CreateShopItemUseCase(repository, self._shop_item_app_mapper)

    def delete_shop_item_use_case(self, session: Session) -> DeleteShopItemUseCase:
        repository = self.shop_item_repository(session)
        return DeleteShopItemUseCase(repository)

    def get_shop_item_use_case(self, session: Session) -> GetShopItemUseCase:
        repository = self.shop_item_repository(session)
        return GetShopItemUseCase(repository, self._shop_item_app_mapper)

    def patch_shop_item_use_case(self, session: Session) -> PatchShopItemUseCase:
        repository = self.shop_item_repository(session)
        return PatchShopItemUseCase(repository, self._shop_item_app_mapper)
