from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ViewerSessionResponse(BaseModel):
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


class ViewerSessionStreamInfo(BaseModel):
    id: int = Field(..., description="Идентификатор стрима")
    title: str | None = Field(None, description="Заголовок стрима")
    game_name: str | None = Field(None, description="Название игры")
    started_at: datetime = Field(..., description="Время начала стрима")
    ended_at: datetime | None = Field(None, description="Время завершения стрима")

    model_config = ConfigDict(from_attributes=True)


class ViewerSessionWithStreamResponse(ViewerSessionResponse):
    stream: ViewerSessionStreamInfo | None = Field(None, description="Информация о стриме")


class ViewerSessionsResponse(BaseModel):
    sessions: list[ViewerSessionWithStreamResponse] = Field(..., description="Список пользовательских сессий")
