from app.joke.application.model.configuration import JokesConfigurationDTO
from app.joke.presentation.api.model.configuration import JokesConfigurationSchema


class JokesConfigurationMapper:
    def map_to_schema(self, configuration: JokesConfigurationDTO) -> JokesConfigurationSchema:
        return JokesConfigurationSchema(
            channel_name=configuration.channel_name,
            interval_min=configuration.interval_min,
            interval_max=configuration.interval_max,
            last_joke_time=configuration.last_joke_time,
            next_joke_time=configuration.next_joke_time,
            is_enabled=configuration.is_enabled,
        )

    def map_to_dto(self, schema: JokesConfigurationSchema) -> JokesConfigurationDTO:
        return JokesConfigurationDTO(
            channel_name=schema.channel_name,
            interval_min=schema.interval_min,
            interval_max=schema.interval_max,
            last_joke_time=schema.last_joke_time,
            next_joke_time=schema.next_joke_time,
            is_enabled=schema.is_enabled,
        )
