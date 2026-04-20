from app.joke.domain.model.configuration import JokesConfiguration
from app.joke.infrastructure.db.configuration import JokesConfigurationRow


class JokesConfigurationMapper:
    def map_to_domain(self, jokes_configuration: JokesConfigurationRow) -> JokesConfiguration:
        return JokesConfiguration(
            channel_name=jokes_configuration.channel_name,
            interval_min=jokes_configuration.interval_min,
            interval_max=jokes_configuration.interval_max,
            last_joke_time=jokes_configuration.last_joke_time,
            next_joke_time=jokes_configuration.next_joke_time,
            is_enabled=jokes_configuration.is_enabled,
        )
