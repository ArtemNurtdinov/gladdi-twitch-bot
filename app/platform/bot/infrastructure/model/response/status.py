from pydantic import BaseModel, Field

from app.platform.bot.infrastructure.model.status import BotStatus


class BotStatusResponse(BaseModel):
    status: BotStatus = Field(..., description="Текущее состояние бота")
    started_at: str | None = Field(None, description="Время запуска в ISO формате")
    last_error: str | None = Field(None, description="Последняя ошибка, если была")
