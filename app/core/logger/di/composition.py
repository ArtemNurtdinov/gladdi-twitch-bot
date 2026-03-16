from functools import lru_cache

from app.core.config.di.composition import load_config
from app.core.logger.di.dependencies import provide_logger
from app.core.logger.domain.logger import Logger


@lru_cache
def get_logger() -> Logger:
    config = load_config()
    return provide_logger(config.logging)
