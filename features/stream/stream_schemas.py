from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class StreamResponse(BaseModel):
    id: int = Field(..., description="Идентификатор стрима")
    channel_name: str = Field(..., description="Название канала")
    started_at: datetime = Field(..., description="Дата и время начала стрима")
    ended_at: datetime | None = Field(None, description="Дата и время окончания стрима")
    game_name: str | None = Field(None, description="Название игры")
    title: str | None = Field(None, description="Заголовок стрима")
    total_viewers: int = Field(..., description="Общее количество зрителей")
    max_concurrent_viewers: int = Field(..., description="Пиковое количество зрителей")
    is_active: bool = Field(..., description="Флаг активности стрима")
    created_at: datetime = Field(..., description="Дата создания записи")
    updated_at: datetime = Field(..., description="Дата последнего обновления записи")

    model_config = ConfigDict(from_attributes=True)


class StreamListResponse(BaseModel):
    items: list[StreamResponse] = Field(..., description="Список стримов")
    total: int = Field(..., description="Общее количество стримов в выборке")
