from dataclasses import dataclass


@dataclass
class JokesSettings:
    jokes_enabled: bool = False
    jokes_interval_min: int = 30
    jokes_interval_max: int = 60
    last_joke_time: str | None = None
    next_joke_time: str | None = None
    last_updated: str | None = None
    version: str = "1.1"
