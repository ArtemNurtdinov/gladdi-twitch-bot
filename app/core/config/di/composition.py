from functools import lru_cache

from app.core.config.di.dependencies import (
    get_config_repository,
    get_config_source,
    get_load_configuration_use_case,
    get_validate_config_use_case,
)
from app.core.config.domain.model.configuration import Config


@lru_cache
def load_config() -> Config:
    source = get_config_source()
    repo = get_config_repository(source)
    validate = get_validate_config_use_case()
    use_case = get_load_configuration_use_case(repo, validate)
    return use_case.execute()
