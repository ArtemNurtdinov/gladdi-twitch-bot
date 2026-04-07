from pydantic import BaseModel

from app.ai.gen.llm.infrastructure.model.response.usage import UsageSchema


class AIResponseSchema(BaseModel):
    assistant_message: str
    usage: UsageSchema = UsageSchema()
