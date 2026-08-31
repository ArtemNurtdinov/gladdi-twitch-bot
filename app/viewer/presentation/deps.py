from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.presentation.deps import get_app
from app.viewer.di.container import ViewerContainer


def get_viewer_container(app: AppContainer = Depends(get_app)) -> ViewerContainer:
    return app.viewer
