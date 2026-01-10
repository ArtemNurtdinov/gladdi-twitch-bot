from pydantic import BaseModel, Field


class AuthStartResponse(BaseModel):
    auth_url: str = Field(..., description="Ссылка для авторизации Twitch")
    message: str = Field(..., description="Дополнительная информация")

