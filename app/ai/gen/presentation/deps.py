from fastapi import Depends

from app.ai.gen.di.container import AIContainer
from app.bootstrap.app_container import AppContainer
from app.presentation.deps import get_app


def get_ai_container(app: AppContainer = Depends(get_app)) -> AIContainer:
    return app.ai
