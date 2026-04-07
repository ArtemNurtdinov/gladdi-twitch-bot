from pydantic import BaseModel, Field


class NextJokeSchema(BaseModel):
    next_joke_time: str | None = Field(None, description="Время следующего анекдота")
    minutes_until_next: int | None = Field(None, description="Осталось времени до следующего анекдота")
