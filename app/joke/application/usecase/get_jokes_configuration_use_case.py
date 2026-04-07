from app.joke.application.mapper.jokes_configuration_mapper import JokesConfigurationMapper
from app.joke.application.model.configuration import JokesConfigurationDTO
from app.joke.domain.repository import JokesConfigurationRepository


class GetJokesConfigurationUseCase:
    def __init__(self, jokes_configuration_repository: JokesConfigurationRepository, mapper: JokesConfigurationMapper):
        self._jokes_configuration_repository = jokes_configuration_repository
        self._mapper = mapper

    def get_configuration(self, channel_name: str) -> JokesConfigurationDTO:
        configuration = self._jokes_configuration_repository.get_current_configuration(channel_name)

        if configuration is None:
            return JokesConfigurationDTO(
                channel_name=channel_name,
                interval_min=30,
                interval_max=60,
                last_joke_time=None,
                next_joke_time=None,
                is_enabled=False,
            )

        return self._mapper.map_to_dto(configuration)
