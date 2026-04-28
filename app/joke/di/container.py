from sqlalchemy.orm import Session

from app.core.logger.domain.logger import Logger
from app.joke.application.mapper.jokes_configuration_mapper import JokesConfigurationMapper as JokesConfigurationDTOMapper
from app.joke.application.usecase.get_jokes_configuration_use_case import GetJokesConfigurationUseCase
from app.joke.application.usecase.save_jokes_configuration_use_case import SaveJokesConfigurationUseCase
from app.joke.domain.repository import JokesConfigurationRepository
from app.joke.infrastructure.mapper.jokes_configuration_mapper import JokesConfigurationMapper as JokesConfigurationDbMapper
from app.joke.infrastructure.repository import JokesConfigurationRepositoryImpl
from app.joke.presentation.api.mapper.jokes_configuration_mapper import JokesConfigurationMapper as JokesConfigurationSchemaMapper
from core.types import SessionFactory


class JokeContainer:
    def __init__(self, session_factory_rw: SessionFactory, session_factory_ro: SessionFactory, logger: Logger):
        self._session_factory_rw = session_factory_rw
        self._session_factory_ro = session_factory_ro
        self.jokes_configuration_db_mapper = JokesConfigurationDbMapper()
        self.jokes_configuration_dto_mapper = JokesConfigurationDTOMapper()
        self.jokes_configuration_schema_mapper = JokesConfigurationSchemaMapper()
        self.logger = logger.create_child(__name__)

    def jokes_configuration_repository(self, session: Session) -> JokesConfigurationRepository:
        return JokesConfigurationRepositoryImpl(session, self.jokes_configuration_db_mapper)

    def get_jokes_configuration_use_case(self, session: Session) -> GetJokesConfigurationUseCase:
        jokes_configuration_repository = self.jokes_configuration_repository(session)
        return GetJokesConfigurationUseCase(jokes_configuration_repository, self.jokes_configuration_dto_mapper)

    def save_jokes_configuration_use_case(self, session: Session) -> SaveJokesConfigurationUseCase:
        jokes_configuration_repository = self.jokes_configuration_repository(session)
        return SaveJokesConfigurationUseCase(jokes_configuration_repository, self.jokes_configuration_dto_mapper)
