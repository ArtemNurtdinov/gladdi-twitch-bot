from pydantic import BaseModel, Field


class JokesIntervalRequest(BaseModel):
    min_minutes: int = Field(..., ge=1, le=300, description="Минимальный интервал в минутах (1-300)")
    max_minutes: int = Field(..., ge=1, le=300, description="Максимальный интервал в минутах (1-300)")
