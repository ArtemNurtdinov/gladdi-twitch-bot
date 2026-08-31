from fastapi import APIRouter, Depends

from app.bot.bot_manager import BotManager
from app.bot.presentation.api.model.response.status import BotStatusResponse
from app.bot.presentation.deps import get_bot_manager

router = APIRouter()


@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(bot_manager: BotManager = Depends(get_bot_manager)) -> BotStatusResponse:
    return bot_manager.get_status()
