from app.core.config.application.usecase.validate_config_use_case import ValidateConfigUseCase
from app.core.config.domain.config_repository import ConfigRepository
from app.core.config.domain.model.configuration import Config


class LoadConfigurationUseCase:
    def __init__(self, config_repository: ConfigRepository, validate_config_use_case: ValidateConfigUseCase):
        self._config_repository = config_repository
        self._validate_config_use_case = validate_config_use_case

    def execute(self) -> Config:
        configuration = self._config_repository.get_config()
        self._validate_config_use_case.validate(configuration)
        return configuration
