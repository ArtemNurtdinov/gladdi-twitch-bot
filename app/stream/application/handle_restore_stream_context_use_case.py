from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.minigame.domain.minigame_service import MinigameService
from app.stream.application.model import RestoreStreamJobDTO
from app.stream.domain.stream_service import StreamService
from core.provider import Provider


class HandleRestoreStreamContextUseCase:
    def __init__(
        self,
        stream_service_provider: Provider[StreamService],
        minigame_service: MinigameService,
        db_readonly_session_provider: Callable[[], AbstractContextManager[Session]],
    ):
        self._stream_service_provider = stream_service_provider
        self._minigame_service = minigame_service
        self._db_readonly_session_provider = db_readonly_session_provider

    def handle(self, restore_stream_job_dto: RestoreStreamJobDTO) -> None:
        with self._db_readonly_session_provider() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(restore_stream_job_dto.channel_name)

        if active_stream:
            self._minigame_service.set_stream_start_time(restore_stream_job_dto.channel_name, active_stream.started_at)
