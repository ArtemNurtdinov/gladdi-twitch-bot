from functools import lru_cache

from fastapi import APIRouter, Depends

from app.bot.bot_manager import BotManager
from app.bot.presentation.api.model.response.status import BotStatusResponse
from app.core.di.application_container import app_container

router = APIRouter()


@lru_cache
def get_bot_manager() -> BotManager:
    return BotManager(
        config=app_container.config.bot,
        telegram_config=app_container.config.telegram,
        llmbox_config=app_container.config.llmbox,
        intent_detector_config=app_container.config.intent_detector,
        logger=app_container.logger,
    )


@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(bot_manager: BotManager = Depends(get_bot_manager)) -> BotStatusResponse:
    return bot_manager.get_status()
