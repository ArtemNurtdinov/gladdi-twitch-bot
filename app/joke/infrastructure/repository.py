from sqlalchemy.orm import Session

from app.joke.domain.model.configuration import JokesConfiguration
from app.joke.domain.repository import JokesConfigurationRepository
from app.joke.infrastructure.db.configuration import JokesConfigurationRow
from app.joke.infrastructure.mapper.jokes_configuration_mapper import JokesConfigurationMapper


class JokesConfigurationRepositoryImpl(JokesConfigurationRepository):
    def __init__(self, session: Session, mapper: JokesConfigurationMapper):
        self._session = session
        self._mapper = mapper

    async def get_current_configuration(self, channel_name: str) -> JokesConfiguration | None:
        row = self._session.query(JokesConfigurationRow).filter(JokesConfigurationRow.channel_name == channel_name).first()

        if row is None:
            return None

        return self._mapper.map_to_domain(row)

    async def save_configuration(self, configuration: JokesConfiguration) -> None:
        row = self._session.query(JokesConfigurationRow).filter(JokesConfigurationRow.channel_name == configuration.channel_name).first()

        if row is None:
            row = JokesConfigurationRow(
                channel_name=configuration.channel_name,
                interval_min=configuration.interval_min,
                interval_max=configuration.interval_max,
                last_joke_time=configuration.last_joke_time,
                next_joke_time=configuration.next_joke_time,
                is_enabled=configuration.is_enabled,
            )
            self._session.add(row)
        else:
            row.interval_min = configuration.interval_min
            row.interval_max = configuration.interval_max
            row.last_joke_time = configuration.last_joke_time
            row.next_joke_time = configuration.next_joke_time
            row.is_enabled = configuration.is_enabled

        self._session.commit()
