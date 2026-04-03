from pydantic import Field

from app.platform.bot.infrastructure.model.response.status import BotStatusResponse


class BotActionResultResponse(BotStatusResponse):
    message: str = Field(..., description="Результат действия")
