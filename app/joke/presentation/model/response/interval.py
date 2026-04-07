from pydantic import Field

from app.joke.presentation.model.interval import JokeIntervalSchema
from app.joke.presentation.model.next_joke import NextJokeSchema


class JokesIntervalResponse(JokeIntervalSchema):
    success: bool = Field(..., description="Успешность операции")
    next_joke: NextJokeSchema | None = Field(..., description="Информация о следующем анекдоте")
