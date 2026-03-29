import os

from app.core.config.domain.config_source import ConfigSource


class EnvConfigSource(ConfigSource):
    def get_str(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)

    def get_int(self, key: str, default: int | None = None) -> int | None:
        return int(os.getenv(key, default))
