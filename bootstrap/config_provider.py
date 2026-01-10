from functools import lru_cache

from core.config import Config, load_config


@lru_cache
def get_config() -> Config:
    return load_config()
