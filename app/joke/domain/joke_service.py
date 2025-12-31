import logging
from datetime import datetime

from app.joke.domain.models import (
    BotSettings,
    JokeIntervalInfo,
    JokesIntervalDto,
    JokesResponseDto,
    JokesStatusDto,
    NextJokeInfo,
)
from app.joke.domain.policies import plan_next_joke_time, should_generate_now, validate_interval
from app.joke.domain.repo import JokeSettingsRepository

logger = logging.getLogger(__name__)


class JokeService:
    def __init__(self, settings_repo: JokeSettingsRepository):
        self.settings_repo = settings_repo

    def _touch_updated(self, settings: BotSettings) -> BotSettings:
        settings.last_updated = datetime.now().isoformat()
        return settings

    def _build_next_joke(self, settings: BotSettings) -> NextJokeInfo | None:
        if not settings.jokes_enabled:
            return None

        can_generate = should_generate_now(settings)
        minutes_until_next = None
        if settings.next_joke_time and not can_generate:
            try:
                next_time = datetime.fromisoformat(settings.next_joke_time)
                diff = next_time - datetime.now()
                minutes_until_next = max(0, int(diff.total_seconds() / 60))
            except ValueError:
                minutes_until_next = None

        return NextJokeInfo(next_joke_time=settings.next_joke_time, minutes_until_next=minutes_until_next)

    def get_jokes_status(self) -> JokesStatusDto:
        settings = self.settings_repo.load()
        joke_interval = JokeIntervalInfo(
            min_minutes=settings.jokes_interval_min,
            max_minutes=settings.jokes_interval_max,
            description=f"Интервал: {settings.jokes_interval_min}-{settings.jokes_interval_max} минут",
        )
        next_joke = self._build_next_joke(settings)
        return JokesStatusDto(
            enabled=settings.jokes_enabled,
            message=f"Анекдоты {'включены' if settings.jokes_enabled else 'отключены'}",
            interval=joke_interval,
            next_joke=next_joke,
        )

    def enable_jokes(self) -> JokesResponseDto:
        try:
            settings = self.settings_repo.load()
            settings.jokes_enabled = True
            settings.next_joke_time = plan_next_joke_time(settings)
            self._touch_updated(settings)
            self.settings_repo.save(settings)
            logger.info("Анекдоты включены")
            return JokesResponseDto(success=True, message="Анекдоты включены")
        except Exception as e:
            logger.error("Ошибка включения анекдотов: %s", e)
            return JokesResponseDto(success=False, message=f"Ошибка включения анекдотов: {str(e)}")

    def disable_jokes(self) -> JokesResponseDto:
        try:
            settings = self.settings_repo.load()
            settings.jokes_enabled = False
            settings.next_joke_time = None
            self._touch_updated(settings)
            self.settings_repo.save(settings)
            logger.info("Анекдоты отключены")
            return JokesResponseDto(success=True, message="Анекдоты отключены")
        except Exception as e:
            logger.error("Ошибка отключения анекдотов: %s", e)
            return JokesResponseDto(success=False, message=f"Ошибка отключения анекдотов: {str(e)}")

    def set_jokes_interval(self, interval_min: int, interval_max: int) -> JokesIntervalDto:
        validate_interval(interval_min, interval_max)
        settings = self.settings_repo.load()
        settings.jokes_interval_min = interval_min
        settings.jokes_interval_max = interval_max

        if settings.jokes_enabled:
            settings.next_joke_time = plan_next_joke_time(settings)
            logger.info("Пересчитано время следующего анекдота: %s", settings.next_joke_time)

        self._touch_updated(settings)
        self.settings_repo.save(settings)

        description = f"Интервал обновлен: {settings.jokes_interval_min}-{settings.jokes_interval_max} минут"
        next_joke_info = self._build_next_joke(settings)

        logger.info("Интервал анекдотов обновлен: %s-%s минут", interval_min, interval_max)
        return JokesIntervalDto(
            success=True,
            min_minutes=settings.jokes_interval_min,
            max_minutes=settings.jokes_interval_max,
            description=description,
            next_joke=next_joke_info,
        )

    def should_generate_jokes(self) -> bool:
        settings = self.settings_repo.load()
        return should_generate_now(settings)

    def mark_joke_generated(self) -> bool:
        settings = self.settings_repo.load()
        if not settings.jokes_enabled:
            return False

        settings.last_joke_time = datetime.now().isoformat()
        settings.next_joke_time = plan_next_joke_time(settings)
        self._touch_updated(settings)
        self.settings_repo.save(settings)
        logger.info("Анекдот сгенерирован, следующий запланирован на %s", settings.next_joke_time)
        return True

    def get_next_joke_info(self) -> NextJokeInfo | None:
        settings = self.settings_repo.load()
        return self._build_next_joke(settings)
