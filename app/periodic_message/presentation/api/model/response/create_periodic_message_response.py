from pydantic import BaseModel, Field

from app.periodic_message.presentation.api.model.periodic_message_schema import PeriodicMessageSchema


class CreatePeriodicMessageResponse(BaseModel):
    periodic_message: PeriodicMessageSchema = Field(..., description="Периодическое сообщение")
