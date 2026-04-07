from app.joke.application.mapper.jokes_configuration_mapper import JokesConfigurationMapper
from app.joke.application.model.configuration import JokesConfigurationDTO
from app.joke.domain.repository import JokesConfigurationRepository


class SaveJokesConfigurationUseCase:
    def __init__(self, jokes_configuration_repository: JokesConfigurationRepository, mapper: JokesConfigurationMapper):
        self._jokes_configuration_repository = jokes_configuration_repository
        self._mapper = mapper

    async def save_configuration(self, configuration: JokesConfigurationDTO) -> None:
        configuration_domain = self._mapper.map_to_domain(configuration)
        await self._jokes_configuration_repository.save_configuration(configuration_domain)
