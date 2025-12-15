from pydantic import BaseModel, Field


class TopChatUser(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    message_count: int = Field(..., description="Количество сообщений")
