from app.minigame.domain.minigame_service import MinigameService
from app.stream.application.model import RestoreStreamJobDTO
from app.stream.application.restore_stream_context_uow import RestoreStreamContextUnitOfWorkFactory


class HandleRestoreStreamContextUseCase:
    def __init__(
        self,
        unit_of_work_factory: RestoreStreamContextUnitOfWorkFactory,
        minigame_service: MinigameService,
    ):
        self._unit_of_work_factory = unit_of_work_factory
        self._minigame_service = minigame_service

    def handle(self, restore_stream_job_dto: RestoreStreamJobDTO) -> None:
        with self._unit_of_work_factory.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(restore_stream_job_dto.channel_name)

        if active_stream:
            self._minigame_service.set_stream_start_time(restore_stream_job_dto.channel_name, active_stream.started_at)
