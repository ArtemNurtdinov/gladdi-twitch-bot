from enum import Enum

from pydantic import BaseModel, Field


class BotStatusEnum(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"


class BotStatus(BaseModel):
    status: BotStatusEnum = Field(..., description="Текущее состояние бота")
    started_at: str | None = Field(None, description="Время запуска в ISO формате")
    last_error: str | None = Field(None, description="Последняя ошибка, если была")


class BotActionResult(BotStatus):
    message: str = Field(..., description="Результат действия")


class AuthStartResponse(BaseModel):
    auth_url: str = Field(..., description="Ссылка для авторизации Twitch")
    message: str = Field(..., description="Дополнительная информация")
