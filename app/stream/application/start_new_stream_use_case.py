import logging
from datetime import datetime

from app.stream.application.start_new_stream_uow import StartNewStreamUnitOfWorkFactory

logger = logging.getLogger(__name__)


class StartNewStreamUseCase:
    def __init__(self, unit_of_work_factory: StartNewStreamUnitOfWorkFactory):
        self._unit_of_work_factory = unit_of_work_factory

    def execute(self, channel_name: str, started_at: datetime, game_name: str | None = None, title: str | None = None):
        with self._unit_of_work_factory.create() as uow:
            active_stream = uow.stream_repo.get_active_stream(channel_name)
            if active_stream:
                logger.warning(f"Попытка начать стрим, но активный стрим уже существует: {active_stream.id}")
                return

            uow.stream_repo.start_new_stream(channel_name, started_at, game_name, title)
