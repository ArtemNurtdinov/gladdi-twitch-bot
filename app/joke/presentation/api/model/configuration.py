from datetime import datetime

from pydantic import BaseModel, Field


class JokesConfigurationSchema(BaseModel):
    channel_name: str = Field(..., description="Название канала")
    interval_min: int = Field(30, ge=1, description="Минимальный интервал в минутах")
    interval_max: int = Field(60, ge=1, description="Максимальный интервал в минутах")
    last_joke_time: datetime | None = Field(None, description="Время последней шутки")
    next_joke_time: datetime | None = Field(None, description="Время следующей шутки")
    is_enabled: bool = Field(False, description="Включена ли отправка шуток")
