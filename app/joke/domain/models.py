from dataclasses import dataclass
from typing import Optional


@dataclass
class BotSettings:
    jokes_enabled: bool = False
    jokes_interval_min: int = 30
    jokes_interval_max: int = 60
    last_joke_time: Optional[str] = None
    next_joke_time: Optional[str] = None
    last_updated: Optional[str] = None
    version: str = "1.1"


@dataclass
class NextJokeInfo:
    next_joke_time: Optional[str]
    minutes_until_next: Optional[int]


@dataclass
class JokeIntervalInfo:
    min_minutes: int
    max_minutes: int
    description: str


@dataclass
class JokesStatusDto:
    enabled: bool
    message: str
    interval: JokeIntervalInfo
    next_joke: Optional[NextJokeInfo]


@dataclass
class JokesResponseDto:
    success: bool
    message: str


@dataclass
class JokesIntervalDto:
    success: bool
    min_minutes: int
    max_minutes: int
    description: str
    next_joke: Optional[NextJokeInfo]
