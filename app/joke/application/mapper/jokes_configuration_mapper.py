from app.joke.application.model.configuration import JokesConfigurationDTO
from app.joke.domain.model.configuration import JokesConfiguration


class JokesConfigurationMapper:
    def map_to_dto(self, configuration: JokesConfiguration) -> JokesConfigurationDTO:
        return JokesConfigurationDTO(
            channel_name=configuration.channel_name,
            interval_min=configuration.interval_min,
            interval_max=configuration.interval_max,
            last_joke_time=configuration.last_joke_time,
            next_joke_time=configuration.next_joke_time,
            is_enabled=configuration.is_enabled,
        )
