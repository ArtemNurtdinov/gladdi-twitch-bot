from pydantic import BaseModel, Field


class CreatePeriodicMessageRequest(BaseModel):
    channel_name: str = Field(..., description="Название канала", min_length=1, max_length=100)
    content: str = Field(..., description="Текст сообщения или промпт для LLM", min_length=1)
    use_llm: bool = Field(False, description="Генерировать текст через LLM")
    interval_minutes: int = Field(..., ge=1, description="Интервал отправки в минутах")
    is_enabled: bool = Field(True, description="Включена ли отправка")
