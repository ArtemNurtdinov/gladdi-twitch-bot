from fastapi import APIRouter, Depends, Request

from app.bot.bot_manager import BotManager
from app.bot.presentation.api.model.response.status import BotStatusResponse

router = APIRouter()


def get_bot_manager(request: Request) -> BotManager:
    return request.app.state.bot_manager


@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(bot_manager: BotManager = Depends(get_bot_manager)) -> BotStatusResponse:
    return bot_manager.get_status()
