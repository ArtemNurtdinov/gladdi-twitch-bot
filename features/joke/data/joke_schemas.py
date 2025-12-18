from pydantic import BaseModel, Field
from typing import Optional


class NextJoke(BaseModel):
    next_joke_time: Optional[str] = Field(None, description="Время следующего анекдота")
    minutes_until_next: Optional[int] = Field(None, description="Осталось времени до следующего анекдота")


class JokeInterval(BaseModel):
    min_minutes: int = Field(..., description="Нижняя граница интервала между анекдотами")
    max_minutes: int = Field(..., description="Верхняя граница интервала между анекдотами")
    description: str = Field(..., description="Описание интервала")


class JokesStatus(BaseModel):
    enabled: bool = Field(..., description="Статус анекдотов (включены/отключены)")
    message: str = Field(..., description="Описание статуса")
    interval: JokeInterval = Field(..., description="Интервал между анекдотами")
    next_joke: Optional[NextJoke] = Field(..., description="Информация о следующем анекдоте")


class JokesResponse(BaseModel):
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение о результате")


class JokesIntervalResponse(JokeInterval):
    success: bool = Field(..., description="Успешность операции")
    next_joke: Optional[NextJoke] = Field(..., description="Информация о следующем анекдоте")


class JokesIntervalRequest(BaseModel):
    min_minutes: int = Field(..., ge=1, le=300, description="Минимальный интервал в минутах (1-300)")
    max_minutes: int = Field(..., ge=1, le=300, description="Максимальный интервал в минутах (1-300)")
