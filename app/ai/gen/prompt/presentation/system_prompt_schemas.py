from pydantic import BaseModel, Field


class SystemPromptResponse(BaseModel):
    channel_name: str = Field(..., description="Название канала")
    content: str = Field(..., description="Системный промпт для канала")


class SystemPromptUpdate(BaseModel):
    content: str = Field(..., description="Новый текст системного промпта")
