from pydantic import BaseModel, Field


class JokeIntervalSchema(BaseModel):
    min_minutes: int = Field(..., description="Нижняя граница интервала между анекдотами")
    max_minutes: int = Field(..., description="Верхняя граница интервала между анекдотами")
    description: str = Field(..., description="Описание интервала")
