from app.joke.application.dto import (
    JokeIntervalDto,
    JokesIntervalResultDto,
    JokesResponseDto,
    JokesStatusDto,
    NextJokeDto,
)
from app.joke.domain.joke_service import JokeService
from app.joke.domain.models import (
    JokeIntervalInfo,
    NextJokeInfo,
)
from app.joke.domain.models import (
    JokesIntervalDto as DomainJokesIntervalDto,
)
from app.joke.domain.models import (
    JokesResponseDto as DomainJokesResponseDto,
)
from app.joke.domain.models import (
    JokesStatusDto as DomainJokesStatusDto,
)


class JokeUseCase:

    def __init__(self, joke_service: JokeService):
        self._service = joke_service

    def _to_next_joke(self, dto: NextJokeInfo | None) -> NextJokeDto | None:
        if dto is None:
            return None
        return NextJokeDto(next_joke_time=dto.next_joke_time, minutes_until_next=dto.minutes_until_next)

    def _to_interval(self, dto: JokeIntervalInfo) -> JokeIntervalDto:
        return JokeIntervalDto(min_minutes=dto.min_minutes, max_minutes=dto.max_minutes, description=dto.description)

    def _to_status(self, dto: DomainJokesStatusDto) -> JokesStatusDto:
        return JokesStatusDto(
            enabled=dto.enabled,
            message=dto.message,
            interval=self._to_interval(dto.interval),
            next_joke=self._to_next_joke(dto.next_joke),
        )

    def _to_response(self, dto: DomainJokesResponseDto) -> JokesResponseDto:
        return JokesResponseDto(success=dto.success, message=dto.message)

    def _to_interval_result(self, dto: DomainJokesIntervalDto) -> JokesIntervalResultDto:
        return JokesIntervalResultDto(
            success=dto.success,
            min_minutes=dto.min_minutes,
            max_minutes=dto.max_minutes,
            description=dto.description,
            next_joke=self._to_next_joke(dto.next_joke),
        )

    def get_jokes_status(self) -> JokesStatusDto:
        return self._to_status(self._service.get_jokes_status())

    def enable_jokes(self) -> JokesResponseDto:
        return self._to_response(self._service.enable_jokes())

    def disable_jokes(self) -> JokesResponseDto:
        return self._to_response(self._service.disable_jokes())

    def set_jokes_interval(self, interval_min: int, interval_max: int) -> JokesIntervalResultDto:
        return self._to_interval_result(self._service.set_jokes_interval(interval_min, interval_max))
