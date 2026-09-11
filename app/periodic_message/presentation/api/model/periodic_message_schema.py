from datetime import datetime

from pydantic import BaseModel, Field


class PeriodicMessageSchema(BaseModel):
    id: int = Field(..., description="ID сообщения")
    channel_name: str = Field(..., description="Название канала")
    content: str = Field(..., description="Текст сообщения или промпт для LLM")
    use_llm: bool = Field(..., description="Генерировать текст через LLM")
    interval_minutes: int = Field(..., ge=1, description="Интервал отправки в минутах")
    is_enabled: bool = Field(..., description="Включена ли отправка")
    last_sent_at: datetime | None = Field(None, description="Время последней отправки")
    next_send_at: datetime | None = Field(None, description="Время следующей отправки")
