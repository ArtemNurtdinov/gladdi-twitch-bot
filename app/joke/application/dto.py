from dataclasses import dataclass


@dataclass(frozen=True)
class NextJokeDto:
    next_joke_time: str | None
    minutes_until_next: int | None


@dataclass(frozen=True)
class JokeIntervalDto:
    min_minutes: int
    max_minutes: int
    description: str


@dataclass(frozen=True)
class JokesStatusDto:
    enabled: bool
    message: str
    interval: JokeIntervalDto
    next_joke: NextJokeDto | None


@dataclass(frozen=True)
class JokesResponseDto:
    success: bool
    message: str


@dataclass(frozen=True)
class JokesIntervalResultDto:
    success: bool
    min_minutes: int
    max_minutes: int
    description: str
    next_joke: NextJokeDto | None
