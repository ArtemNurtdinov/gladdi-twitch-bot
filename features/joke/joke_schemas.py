from pydantic import BaseModel, Field
from typing import Dict, Any


class JokeInterval(BaseModel):
    min_minutes: int = Field(..., description="Нижняя граница интервала между анекдотами")
    max_minutes: int = Field(..., description="Верхняя граница интервала между анекдотами")
    description: str = Field(..., description="Описание интервала")


class JokesStatus(BaseModel):
    enabled: bool = Field(..., description="Статус анекдотов (включены/отключены)")
    ready: bool = Field(..., description="Готовность бота")
    message: str = Field(..., description="Описание статуса")
    interval: JokeInterval = Field(..., description="Интервал между анекдотами")
    next_joke: Dict[str, Any] = Field(..., description="Информация о следующем анекдоте")


class JokesResponse(BaseModel):
    success: bool = Field(..., description="Успешность операции")
    enabled: bool = Field(..., description="Статус анекдотов после операции")
    message: str = Field(..., description="Сообщение о результате")


class JokesIntervalInfo(BaseModel):
    min_minutes: int = Field(..., description="Минимальный интервал в минутах")
    max_minutes: int = Field(..., description="Максимальный интервал в минутах")
    description: str = Field(..., description="Описание интервала")
    next_joke: Dict[str, Any] = Field(..., description="Информация о следующем анекдоте")


class JokesIntervalResponse(BaseModel):
    success: bool = Field(..., description="Успешность операции")
    min_minutes: int = Field(..., description="Минимальный интервал после операции")
    max_minutes: int = Field(..., description="Максимальный интервал после операции")
    description: str = Field(..., description="Описание результата")
    next_joke: Dict[str, Any] = Field(..., description="Информация о следующем анекдоте")


class JokesIntervalRequest(BaseModel):
    min_minutes: int = Field(..., ge=1, le=300, description="Минимальный интервал в минутах (1-300)")
    max_minutes: int = Field(..., ge=1, le=300, description="Максимальный интервал в минутах (1-300)")
