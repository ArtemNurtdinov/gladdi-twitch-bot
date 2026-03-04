import enum

from pydantic import BaseModel, Field


class BotStatusEnum(enum.StrEnum):
    RUNNING = "running"
    STOPPED = "stopped"


class BotStatus(BaseModel):
    status: BotStatusEnum = Field(..., description="Текущее состояние бота")
    started_at: str | None = Field(None, description="Время запуска в ISO формате")
    last_error: str | None = Field(None, description="Последняя ошибка, если была")


class BotActionResult(BotStatus):
    message: str = Field(..., description="Результат действия")
