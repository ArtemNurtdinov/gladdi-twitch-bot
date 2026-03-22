from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.commands.commands_registry import CommandRegistry
from app.commands.guess.infrastructure.rps_command_handler import RpsCommandHandlerImpl
from app.minigame.application.use_case.handle_rps_use_case import HandleRpsUseCase
from app.platform.bot.model.bot_settings import BotSettings
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories


def build_command_registry(
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
    bot_name: str,
    send_channel_message: Callable[[str], Awaitable[None]],
) -> CommandRegistry:
    prefix = settings.prefix

    rps_command_handler = RpsCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_rps,
        handle_rps_use_case=HandleRpsUseCase(
            minigame_repository=providers.minigame_providers.minigame_repository,
            rps_uow=uow_factories.build_rps_uow_factory(),
        ),
        bot_nick=bot_name,
        post_message_fn=send_channel_message,
    )

    return CommandRegistry(
        rps_command_handler=rps_command_handler,
    )
