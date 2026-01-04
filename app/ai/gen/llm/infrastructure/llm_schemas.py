from pydantic import BaseModel


class UsageSchema(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    class Config:
        extra = "ignore"


class AIResponseSchema(BaseModel):
    assistant_message: str
    usage: UsageSchema = UsageSchema()

    class Config:
        extra = "ignore"
