from pydantic import BaseModel, Field


class AssistantResponse(BaseModel):
    channel_name: str = Field(..., description="Название канала")
    assistant: str = Field(..., description="LLM-ассистент канала")


class AssistantUpdate(BaseModel):
    assistant: str = Field(..., description="LLM-ассистент канала")
