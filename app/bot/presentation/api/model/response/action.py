from pydantic import Field

from app.bot.presentation.api.model.response.status import BotStatusResponse


class BotActionResultResponse(BotStatusResponse):
    message: str = Field(..., description="Результат действия")
