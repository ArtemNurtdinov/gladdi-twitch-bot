from pydantic import BaseModel, Field

from app.joke.presentation.model.interval import JokeIntervalSchema
from app.joke.presentation.model.next_joke import NextJokeSchema


class JokesStatusResponse(BaseModel):
    enabled: bool = Field(..., description="Статус анекдотов (включены/отключены)")
    message: str = Field(..., description="Описание статуса")
    interval: JokeIntervalSchema = Field(..., description="Интервал между анекдотами")
    next_joke: NextJokeSchema | None = Field(..., description="Информация о следующем анекдоте")
