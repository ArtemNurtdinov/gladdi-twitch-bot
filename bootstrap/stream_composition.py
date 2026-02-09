from __future__ import annotations

from app.platform.bot.bot_settings import BotSettings
from app.stream.application.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.application.model import RestoreStreamJobDTO
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories


def restore_stream_context(
    *,
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
) -> None:
    if not settings.channel_name:
        return
    restore_stream_job_dto = RestoreStreamJobDTO(settings.channel_name)
    HandleRestoreStreamContextUseCase(
        unit_of_work_factory=uow_factories.build_restore_stream_context_uow_factory(),
        minigame_service=providers.minigame_providers.minigame_service,
    ).handle(restore_stream_job_dto)
