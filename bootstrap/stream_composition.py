from __future__ import annotations

from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories


def restore_stream_context(
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    channel_name: str,
) -> None:
    HandleRestoreStreamContextUseCase(
        restore_stream_uow=uow_factories.build_restore_stream_context_uow_factory(),
        minigame_service=providers.minigame_providers.minigame_service,
    ).handle(channel_name)
