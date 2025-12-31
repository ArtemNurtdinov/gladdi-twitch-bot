from pydantic import BaseModel, Field


class UserBetStats(BaseModel):
    total_bets: int = Field(..., description="Количество ставок")
    jackpots: int = Field(None, description="Количество джекпотов")
    jackpot_rate: float | int = Field(None, description="Коэффициент джекпотов")
