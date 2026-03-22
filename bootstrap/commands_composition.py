from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.commands.commands_registry import CommandRegistry
from app.commands.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.commands.guess.infrastructure.guess_command_handler import GuessCommandHandlerImpl
from app.commands.guess.infrastructure.rps_command_handler import RpsCommandHandlerImpl
from app.commands.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.commands.stats.infrastructure.stats_command_handler import StatsCommandHandlerImpl
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

    stats_command_handler = StatsCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_stats,
        handle_stats_use_case=HandleStatsUseCase(
            stats_uow=uow_factories.build_stats_uow_factory(),
        ),
        bot_name=bot_name,
        post_message_fn=send_channel_message,
    )

    guess_command_handler = GuessCommandHandlerImpl(
        command_prefix=prefix,
        command_guess=settings.command_guess,
        command_guess_letter=settings.command_guess_letter,
        command_guess_word=settings.command_guess_word,
        handle_guess_use_case=HandleGuessUseCase(
            minigame_repository=providers.minigame_providers.minigame_repository,
            guess_uow=uow_factories.build_guess_uow_factory(),
        ),
        bot_nick=bot_name,
        post_message_fn=send_channel_message,
    )
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
        stats_command_handler=stats_command_handler,
        help_command_handler=help_command_handler,
        guess_command_handler=guess_command_handler,
        rps_command_handler=rps_command_handler,
    )
