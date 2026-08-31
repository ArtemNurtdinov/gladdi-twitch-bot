from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.bot.bot_manager import BotManager
from app.presentation.deps import get_app


def get_bot_manager(app: AppContainer = Depends(get_app)) -> BotManager:
    return app.bot_manager
