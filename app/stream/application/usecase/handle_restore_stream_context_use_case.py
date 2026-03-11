from app.minigame.domain.minigame_repository import MinigameRepository
from app.stream.application.uow.restore_stream_context_uow import RestoreStreamContextUnitOfWorkFactory


class HandleRestoreStreamContextUseCase:
    def __init__(
        self,
        restore_stream_uow: RestoreStreamContextUnitOfWorkFactory,
        minigame_repository: MinigameRepository,
    ):
        self._restore_stream_uow = restore_stream_uow
        self._minigame_repository = minigame_repository

    def handle(self, channel_name: str) -> None:
        with self._restore_stream_uow.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(channel_name)

        if active_stream:
            self._minigame_repository.set_stream_start_time(channel_name, active_stream.started_at)
            print(f"handle stream restore for {channel_name}: {active_stream.started_at}")
