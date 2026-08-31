from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.platform.di.container import PlatformContainer
from app.presentation.deps import get_app


def get_platform_container(app: AppContainer = Depends(get_app)) -> PlatformContainer:
    return app.platform
