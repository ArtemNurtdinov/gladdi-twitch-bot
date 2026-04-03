from functools import lru_cache

from fastapi import APIRouter, Depends

from app.core.config.di.composition import load_config
from app.core.config.domain.model.configuration import Config
from app.core.logger.di.composition import get_logger
from app.core.logger.domain.logger import Logger
from app.platform.bot.bot_manager import BotManager
from app.platform.bot.infrastructure.model.response.status import BotStatusResponse
from app.platform.bot.model.bot_settings import BotSettings, DefaultBotSettings

router = APIRouter()


@lru_cache
def get_bot_settings(config: Config = Depends(load_config)) -> BotSettings:
    group_id = config.telegram.group_id
    settings = DefaultBotSettings(group_id=group_id)
    return settings


@lru_cache
def get_bot_manager(settings: BotSettings = Depends(get_bot_settings), logger: Logger = Depends(get_logger)) -> BotManager:
    return BotManager(settings=settings, logger=logger)


@router.get("/status", summary="Получить состояние бота", response_model=BotStatusResponse)
async def get_bot_status(bot_manager: BotManager = Depends(get_bot_manager)) -> BotStatusResponse:
    return bot_manager.get_status()
