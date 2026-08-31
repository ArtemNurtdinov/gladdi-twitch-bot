from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.economy.di.container import EconomyContainer
from app.presentation.deps import get_app


def get_economy_container(app: AppContainer = Depends(get_app)) -> EconomyContainer:
    return app.economy
