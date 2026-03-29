from functools import lru_cache

from app.core.config.application.usecase.load_configuration_use_case import LoadConfigurationUseCase
from app.core.config.application.usecase.validate_config_use_case import ValidateConfigUseCase
from app.core.config.domain.config_repository import ConfigRepository
from app.core.config.domain.config_source import ConfigSource
from app.core.config.domain.model.configuration import Config
from app.core.config.infrastructure.config_repository import ConfigRepositoryImpl
from app.core.config.infrastructure.config_source import EnvConfigSource
from app.core.logger.domain.logger import Logger
from app.core.logger.infrastructure.logger import LoggerImpl


@lru_cache
def get_logger() -> Logger:
    config = load_config()
    return LoggerImpl("bootstrap", config.logging)


def get_config_source() -> ConfigSource:
    return EnvConfigSource()


def get_config_repository() -> ConfigRepository:
    source: ConfigSource = get_config_source()
    return ConfigRepositoryImpl(source)


def get_validate_config_use_case() -> ValidateConfigUseCase:
    return ValidateConfigUseCase()


def get_load_configuration_use_case() -> LoadConfigurationUseCase:
    config_repository: ConfigRepository = get_config_repository()
    validate_config_use_case: ValidateConfigUseCase = get_validate_config_use_case()
    return LoadConfigurationUseCase(config_repository, validate_config_use_case)


@lru_cache
def load_config() -> Config:
    load_configuration_use_case: LoadConfigurationUseCase = get_load_configuration_use_case()
    return load_configuration_use_case.execute()
