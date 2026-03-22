from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.ai.gen.application.use_cases.chat_response_use_case import ChatResponseUseCase
from app.commands.balance.application.balance_command_handler import BalanceCommandHandler
from app.commands.balance.application.handle_balance_use_case import HandleBalanceUseCase
from app.commands.balance.infrastructure.balance_command_handler import BalanceCommandHandlerImpl
from app.commands.battle.application.battle_command_handler import BattleCommandHandler
from app.commands.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.commands.battle.infrastructure.battle_command_handler import BattleCommandHandlerImpl
from app.commands.bonus.application.bonus_command_handler import BonusCommandHandler
from app.commands.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.commands.bonus.infrastructure.bonus_command_handler import BonusCommandHandlerImpl
from app.commands.commands_registry import CommandRegistry
from app.commands.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.commands.equipment.infrastructure.equipment_command_handler import EquipmentCommandHandlerImpl
from app.commands.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.commands.guess.infrastructure.guess_command_handler import GuessCommandHandlerImpl
from app.commands.guess.infrastructure.rps_command_handler import RpsCommandHandlerImpl
from app.commands.help.application.handle_help_use_case import HandleHelpUseCase
from app.commands.help.infrastructure.help_command_handler import HelpCommandHandlerImpl
from app.commands.roll.application.handle_roll_use_case import HandleRollUseCase
from app.commands.roll.infrastructure.roll_command_handler import RollCommandHandlerImpl
from app.commands.shop.application.handle_shop_use_case import HandleShopUseCase
from app.commands.shop.application.shop_command_handler import ShopCommandHandler
from app.commands.shop.infrastructure.shop_command_handler import ShopCommandHandlerImpl
from app.commands.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.commands.stats.infrastructure.stats_command_handler import StatsCommandHandlerImpl
from app.commands.top_bottom.application.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.commands.top_bottom.infrastructure.top_bottom_command_handler import TopBottomCommandHandlerImpl
from app.commands.transfer.application.handle_transfer_use_case import HandleTransferUseCase
from app.commands.transfer.application.transfer_command_handler import TransferCommandHandler
from app.commands.transfer.infrastructure.transfer_command_handler import TransferCommandHandlerImpl
from app.minigame.application.use_case.handle_rps_use_case import HandleRpsUseCase
from app.moderation.application.moderation_service import ModerationService
from app.platform.bot.model.bot_settings import BotSettings
from app.platform.domain.repository import PlatformRepository
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories


def build_command_registry(
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
    bot_name: str,
    chat_response_use_case: ChatResponseUseCase,
    platform_repository: PlatformRepository,
    send_channel_message: Callable[[str], Awaitable[None]],
) -> CommandRegistry:
    prefix = settings.prefix
    moderation_service = ModerationService(
        platform_repository=platform_repository,
        user_cache=providers.user_providers.user_cache,
    )

    battle_command_handler: BattleCommandHandler = BattleCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_fight,
        handle_battle_use_case=HandleBattleUseCase(
            battle_uow=uow_factories.build_battle_uow_factory(),
            chat_response_use_case=chat_response_use_case,
            calculate_timeout_use_case=providers.equipment_providers.calculate_timeout_use_case,
        ),
        chat_moderation=moderation_service,
        bot_name=bot_name,
        post_message_fn=send_channel_message,
    )
    roll_command_handler = RollCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_roll,
        handle_roll_use_case=HandleRollUseCase(
            unit_of_work_factory=uow_factories.build_roll_uow_factory(),
            roll_cooldown_use_case_provider=providers.equipment_providers.roll_cooldown_use_case_provider,
            calculate_timeout_use_case=providers.equipment_providers.calculate_timeout_use_case,
        ),
        chat_moderation=moderation_service,
        bot_nick=bot_name,
        post_message_fn=send_channel_message,
    )
    balance_command_handler: BalanceCommandHandler = BalanceCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_balance,
        handle_balance_use_case=HandleBalanceUseCase(
            balance_uow=uow_factories.build_balance_uow_factory(),
        ),
        bot_name=bot_name,
        post_message_fn=send_channel_message,
    )
    bonus_command_handler: BonusCommandHandler = BonusCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_bonus,
        handle_bonus_use_case=HandleBonusUseCase(
            bonus_uow=uow_factories.build_bonus_uow_factory(),
        ),
        bot_name=bot_name,
        post_message_fn=send_channel_message,
    )
    transfer_command_handler: TransferCommandHandler = TransferCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_transfer,
        handle_transfer_use_case=HandleTransferUseCase(
            unit_of_work_factory=uow_factories.build_transfer_uow_factory(),
        ),
        bot_nick=bot_name,
        post_message_fn=send_channel_message,
    )
    shop_command_handler: ShopCommandHandler = ShopCommandHandlerImpl(
        command_prefix=prefix,
        command_shop_name=settings.command_shop,
        command_buy_name=settings.command_buy,
        handle_shop_use_case=HandleShopUseCase(
            unit_of_work_factory=uow_factories.build_shop_uow_factory(),
        ),
        bot_nick=bot_name,
        post_message_fn=send_channel_message,
    )
    equipment_command_handler = EquipmentCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_equipment,
        command_shop=settings.command_shop,
        handle_equipment_use_case=HandleEquipmentUseCase(
            unit_of_work_factory=uow_factories.build_equipment_uow_factory(),
        ),
        bot_name=bot_name,
        post_message_fn=send_channel_message,
    )
    top_bottom_command_handler = TopBottomCommandHandlerImpl(
        command_prefix=prefix,
        command_top=settings.command_top,
        command_bottom=settings.command_bottom,
        handle_top_bottom_use_case=HandleTopBottomUseCase(
            unit_of_work_factory=uow_factories.build_top_bottom_uow_factory(),
        ),
        bot_nick=bot_name,
        post_message_fn=send_channel_message,
    )
    stats_command_handler = StatsCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_stats,
        handle_stats_use_case=HandleStatsUseCase(
            stats_uow=uow_factories.build_stats_uow_factory(),
        ),
        bot_name=bot_name,
        post_message_fn=send_channel_message,
    )
    commands = {
        settings.command_balance,
        settings.command_bonus,
        f"{settings.command_roll} [сумма]",
        f"{settings.command_transfer} @ник сумма",
        settings.command_shop,
        f"{settings.command_buy} название",
        settings.command_equipment,
        settings.command_top,
        settings.command_bottom,
        settings.command_stats,
        settings.command_fight,
        f"{settings.command_gladdi} текст",
        settings.command_followage,
    }
    help_command_handler = HelpCommandHandlerImpl(
        command_prefix=prefix,
        command_name=settings.command_help,
        handle_help_use_case=HandleHelpUseCase(unit_of_work_factory=uow_factories.build_help_uow_factory()),
        commands=commands,
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
        ask_command_handler=ask_command_handler,
        battle_command_handler=battle_command_handler,
        roll_command_handler=roll_command_handler,
        balance_command_handler=balance_command_handler,
        bonus_command_handler=bonus_command_handler,
        transfer_command_handler=transfer_command_handler,
        shop_command_handler=shop_command_handler,
        equipment_command_handler=equipment_command_handler,
        top_bottom_command_handler=top_bottom_command_handler,
        stats_command_handler=stats_command_handler,
        help_command_handler=help_command_handler,
        guess_command_handler=guess_command_handler,
        rps_command_handler=rps_command_handler,
    )
