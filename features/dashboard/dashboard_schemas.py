from pydantic import BaseModel, Field
from typing import List, Dict, Any


class TopUser(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    message_count: int = Field(..., description="Количество сообщений")


class JokesStatus(BaseModel):
    enabled: bool = Field(..., description="Статус анекдотов (включены/отключены)")
    ready: bool = Field(..., description="Готовность бота")
    message: str = Field(..., description="Описание статуса")
    interval: Dict[str, Any] = Field(..., description="Интервал между анекдотами")
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
