from fastapi import Depends

from app.auth.di.container import AuthContainer
from app.bootstrap.app_container import AppContainer
from app.presentation.deps import get_app


def get_auth_container(app: AppContainer = Depends(get_app)) -> AuthContainer:
    return app.auth
