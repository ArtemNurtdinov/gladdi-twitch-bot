from functools import cached_property

from app.core.config.application.usecase.load_configuration_use_case import LoadConfigurationUseCase
from app.core.config.application.usecase.validate_config_use_case import ValidateConfigUseCase
from app.core.config.domain.config_repository import ConfigRepository
from app.core.config.domain.config_source import ConfigSource
from app.core.config.domain.model.configuration import Config
from app.core.config.infrastructure.config_repository import ConfigRepositoryImpl
from app.core.config.infrastructure.config_source import EnvConfigSource
from app.core.logger.domain.logger import Logger
from app.core.logger.infrastructure.logger import LoggerImpl


class ApplicationContainer:
    def __init__(self):
        self.config_source: ConfigSource = EnvConfigSource()
        self.config_repository: ConfigRepository = ConfigRepositoryImpl(self.config_source)
        self.validate_config_use_case = ValidateConfigUseCase()
        self.load_configuration_use_case = LoadConfigurationUseCase(self.config_repository, self.validate_config_use_case)

    @cached_property
    def config(self) -> Config:
        return self.load_configuration_use_case.execute()

    @cached_property
    def logger(self) -> Logger:
        config = self.config
        return LoggerImpl("gladdi", config.logging)
