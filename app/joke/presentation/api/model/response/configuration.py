from pydantic import BaseModel, Field

from app.joke.presentation.api.model.configuration import JokesConfigurationSchema


class JokesConfigurationResponse(BaseModel):
    jokes_configuration: JokesConfigurationSchema = Field(..., description="Конфигурация анекдотов")
