import logging
from datetime import datetime

from app.stream.domain.repo import StreamRepository

logger = logging.getLogger(__name__)


class StartNewStreamUseCase:
    def __init__(self, repo: StreamRepository):
        self._repo = repo

    def execute(self, channel_name: str, started_at: datetime, game_name: str | None = None, title: str | None = None):
        active_stream = self._repo.get_active_stream(channel_name)
        if active_stream:
            logger.warning(f"Попытка начать стрим, но активный стрим уже существует: {active_stream.id}")
            return

        self._repo.start_new_stream(channel_name, started_at, game_name, title)
