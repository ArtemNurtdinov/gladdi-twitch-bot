from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.periodic_message.di.container import PeriodicMessageContainer
from app.presentation.deps import get_app


def get_periodic_message_container(app: AppContainer = Depends(get_app)) -> PeriodicMessageContainer:
    return app.periodic_message
