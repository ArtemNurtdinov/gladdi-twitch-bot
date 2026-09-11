from pydantic import BaseModel, Field

from app.periodic_message.presentation.api.model.periodic_message_schema import PeriodicMessageSchema


class AllPeriodicMessagesResponse(BaseModel):
    periodic_messages: list[PeriodicMessageSchema] = Field(..., description="Список периодических сообщений")
