from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StreamViewerSessionResponse(BaseModel):
    id: int = Field(..., description="Идентификатор сессии")
    stream_id: int = Field(..., description="Идентификатор стрима")
    channel_name: str = Field(..., description="Название канала")
    user_name: str = Field(..., description="Имя пользователя")
    session_start: datetime | None = Field(None, description="Время начала текущей сессии")
    session_end: datetime | None = Field(None, description="Время завершения текущей сессии")
    total_minutes: int = Field(..., description="Накопленное время просмотра в минутах")
    last_activity: datetime | None = Field(None, description="Время последней активности")
    is_watching: bool = Field(..., description="Флаг активности просмотра")
    rewards_claimed: str = Field(..., description="Идентификаторы полученных наград через запятую")
    last_reward_claimed: datetime | None = Field(None, description="Время получения последней награды")
    created_at: datetime = Field(..., description="Дата создания записи")
    updated_at: datetime = Field(..., description="Дата последнего обновления записи")

    model_config = ConfigDict(from_attributes=True)


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


class StreamDetailResponse(StreamResponse):
    viewer_sessions: list[StreamViewerSessionResponse] = Field(default_factory=list, description="Список сессий зрителей для стрима")


class StreamListResponse(BaseModel):
    items: list[StreamResponse] = Field(..., description="Список стримов")
    total: int = Field(..., description="Общее количество стримов в выборке")
