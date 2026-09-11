from pydantic import BaseModel, Field


class PatchPeriodicMessageRequest(BaseModel):
    id: int = Field(..., description="ID сообщения")
    content: str | None = Field(None, description="Текст сообщения или промпт для LLM", min_length=1)
    use_llm: bool | None = Field(None, description="Генерировать текст через LLM")
    interval_minutes: int | None = Field(None, ge=1, description="Интервал отправки в минутах")
    is_enabled: bool | None = Field(None, description="Включена ли отправка")
