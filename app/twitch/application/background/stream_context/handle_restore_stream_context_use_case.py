from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.minigame.domain.minigame_service import MinigameService
from app.twitch.application.shared import StreamServiceProvider


class HandleRestoreStreamContextUseCase:

    def __init__(
        self,
        stream_service_provider: StreamServiceProvider,
        minigame_service: MinigameService,
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
    ):
        self._stream_service_provider = stream_service_provider
        self._minigame_service = minigame_service
        self._db_readonly_session_provider = db_readonly_session_provider

    def handle(self, channel_name: str) -> None:
        with self._db_readonly_session_provider() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(channel_name)

        if active_stream:
            self._minigame_service.set_stream_start_time(channel_name, active_stream.started_at)
