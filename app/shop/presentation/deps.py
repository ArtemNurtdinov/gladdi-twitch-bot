from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.presentation.deps import get_app
from app.shop.di.container import ShopContainer


def get_shop_container(app: AppContainer = Depends(get_app)) -> ShopContainer:
    return app.shop
