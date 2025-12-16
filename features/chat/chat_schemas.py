from pydantic import BaseModel, Field


class TopChatUser(BaseModel):
    channel_name: str = Field(..., description="Название канала")
    username: str = Field(..., description="Имя пользователя")
    message_count: int = Field(..., description="Количество сообщений")


class TopChatUsersResponse(BaseModel):
    top_users: list[TopChatUser] = Field(..., description="Список пользователей с наибольшим количеством сообщений")