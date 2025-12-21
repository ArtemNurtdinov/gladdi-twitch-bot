from datetime import datetime, timedelta
from random import randint

from app.joke.domain.models import BotSettings


def validate_interval(interval_min: int, interval_max: int) -> None:
    if not 1 <= interval_min <= 300:
        raise ValueError("jokes_interval_min должен быть в диапазоне 1-300 минут")
    if not 1 <= interval_max <= 300:
        raise ValueError("jokes_interval_max должен быть в диапазоне 1-300 минут")
    if interval_min > interval_max:
        raise ValueError(f"Минимальный интервал ({interval_min}) не может быть больше максимального ({interval_max})")


def plan_next_joke_time(settings: BotSettings, now: datetime | None = None) -> str:
    """Возвращает iso-время следующего анекдота, используя интервалы настроек."""
    now = now or datetime.now()
    interval_minutes = randint(settings.jokes_interval_min, settings.jokes_interval_max)
    return (now + timedelta(minutes=interval_minutes)).isoformat()


def should_generate_now(settings: BotSettings, now: datetime | None = None) -> bool:
    if not settings.jokes_enabled:
        return False

    if not settings.next_joke_time:
        return True

    now = now or datetime.now()
    try:
        next_time = datetime.fromisoformat(settings.next_joke_time)
        return now >= next_time
    except ValueError:
        return True






