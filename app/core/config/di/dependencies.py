from app.core.config.application.usecase.load_configuration_use_case import LoadConfigurationUseCase
from app.core.config.application.usecase.validate_config_use_case import ValidateConfigUseCase
from app.core.config.domain.config_repository import ConfigRepository
from app.core.config.domain.config_source import ConfigSource
from app.core.config.infrastructure.config_repository import ConfigRepositoryImpl
from app.core.config.infrastructure.config_source import EnvConfigSource


def get_config_source() -> ConfigSource:
    return EnvConfigSource()


def get_config_repository(source: ConfigSource) -> ConfigRepository:
    return ConfigRepositoryImpl(source)


def get_validate_config_use_case() -> ValidateConfigUseCase:
    return ValidateConfigUseCase()


def get_load_configuration_use_case(
    config_repository: ConfigRepository, validate_config_use_case: ValidateConfigUseCase
) -> LoadConfigurationUseCase:
    return LoadConfigurationUseCase(config_repository, validate_config_use_case)
