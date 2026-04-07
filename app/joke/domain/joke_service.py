from datetime import datetime, timedelta
from random import randint

from app.core.logger.domain.logger import Logger
from app.joke.domain.model.joke_settings import JokesSettings
from app.joke.domain.policies import should_generate_now
from app.joke.domain.repo import JokeSettingsRepository


class JokeService:
    def __init__(self, settings_repo: JokeSettingsRepository, logger: Logger):
        self.settings_repo = settings_repo
        self._logger = logger.create_child(__name__)

    def _touch_updated(self, settings: JokesSettings) -> JokesSettings:
        settings.last_updated = datetime.now().isoformat()
        return settings

    def should_generate_jokes(self) -> bool:
        settings = self.settings_repo.load()
        return should_generate_now(settings)

    def mark_joke_generated(self) -> bool:
        settings = self.settings_repo.load()
        if not settings.jokes_enabled:
            return False

        settings.last_joke_time = datetime.now().isoformat()
        settings.next_joke_time = self.plan_next_joke_time(settings)
        self._touch_updated(settings)
        self.settings_repo.save(settings)
        self._logger.log_info(f"Анекдот сгенерирован, следующий запланирован на {settings.next_joke_time}")
        return True

    def plan_next_joke_time(self, settings: JokesSettings, now: datetime | None = None) -> str:
        now = now or datetime.now()
        interval_minutes = randint(settings.jokes_interval_min, settings.jokes_interval_max)
        return (now + timedelta(minutes=interval_minutes)).isoformat()
