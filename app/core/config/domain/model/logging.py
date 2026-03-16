from dataclasses import dataclass


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    file: str
    format: str
