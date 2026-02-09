from __future__ import annotations

from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.commands.application.commands_registry import CommandRegistryProtocol
from app.commands.ask.application.handle_ask_use_case import HandleAskUseCase
from app.commands.ask.presentation.ask_command_handler import AskCommandHandler
from app.commands.balance.application.handle_balance_use_case import HandleBalanceUseCase
from app.commands.balance.presentation.balance_command_handler import BalanceCommandHandler
from app.commands.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.commands.battle.presentation.battle_command_handler import BattleCommandHandler
from app.commands.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.commands.bonus.presentation.bonus_command_handler import BonusCommandHandler
from app.commands.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.commands.equipment.presentation.equipment_command_handler import EquipmentCommandHandler
from app.commands.follow.application.get_followage_use_case import GetFollowageUseCase
from app.commands.follow.application.handle_followage_use_case import HandleFollowAgeUseCase
from app.commands.follow.infrastructure.followage_uow import SimpleFollowageUnitOfWorkFactory
from app.commands.follow.presentation.followage_command_handler import FollowageCommandHandler
from app.commands.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.commands.guess.presentation.guess_command_handler import GuessCommandHandler
from app.commands.guess.presentation.rps_command_handler import RpsCommandHandler
from app.commands.help.application.handle_help_use_case import HandleHelpUseCase
from app.commands.help.presentation.help_command_handler import HelpCommandHandler
from app.commands.presentation.commands_registry import CommandRegistry
from app.commands.roll.application.handle_roll_use_case import HandleRollUseCase
from app.commands.roll.presentation.roll_command_handler import RollCommandHandler
from app.commands.shop.application.handle_shop_use_case import HandleShopUseCase
from app.commands.shop.presentation.shop_command_handler import ShopCommandHandler
from app.commands.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.commands.stats.presentation.stats_command_handler import StatsCommandHandler
from app.commands.top_bottom.application.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.commands.top_bottom.presentation.top_bottom_command_handler import TopBottomCommandHandler
from app.commands.transfer.application.handle_transfer_use_case import HandleTransferUseCase
from app.commands.transfer.presentation.transfer_command_handler import TransferCommandHandler
from app.minigame.application.handle_rps_use_case import HandleRpsUseCase
from app.moderation.application.moderation_service import ModerationService
from app.platform.bot.bot import Bot
from app.platform.bot.bot_settings import BotSettings
from app.platform.streaming import StreamingPlatformPort
from bootstrap.providers_bundle import ProvidersBundle
from bootstrap.uow_composition import UowFactories
from core.chat.outbound import ChatOutbound


def build_command_registry(
    *,
    providers: ProvidersBundle,
    uow_factories: UowFactories,
    settings: BotSettings,
    bot: Bot,
    chat_response_use_case: ChatResponseUseCase,
    system_prompt: str,
    streaming_platform: StreamingPlatformPort,
    outbound: ChatOutbound,
) -> CommandRegistryProtocol:
    prefix = settings.prefix
    post_message_fn = outbound.post_message
    moderation_service = ModerationService(
        moderation_port=streaming_platform,
        user_cache=providers.user_providers.user_cache,
    )
    ask_uow_factory = uow_factories.build_ask_uow_factory()

    followage_command_handler = FollowageCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_followage,
        handle_follow_age_use_case=HandleFollowAgeUseCase(
            chat_repo_provider=providers.chat_providers.chat_repo_provider,
            conversation_repo_provider=providers.ai_providers.conversation_repo_provider,
            get_followage_use_case=GetFollowageUseCase(
                unit_of_work_factory=SimpleFollowageUnitOfWorkFactory(providers.follow_providers.followage_port),
            ),
            chat_response_use_case=chat_response_use_case,
            unit_of_work_factory=uow_factories.build_follow_age_uow_factory(),
            system_prompt=system_prompt,
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    ask_command_handler = AskCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_gladdi,
        handle_ask_use_case=HandleAskUseCase(
            get_intent_from_text_use_case=providers.ai_providers.get_intent_use_case,
            prompt_service=providers.ai_providers.prompt_service,
            unit_of_work_factory=ask_uow_factory,
            system_prompt=system_prompt,
            chat_response_use_case=chat_response_use_case,
        ),
        post_message_fn=post_message_fn,
        bot_nick=bot.nick,
    )
    battle_command_handler = BattleCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_fight,
        handle_battle_use_case=HandleBattleUseCase(
            unit_of_work_factory=uow_factories.build_battle_uow_factory(),
            chat_response_use_case=chat_response_use_case,
            calculate_timeout_use_case_provider=providers.equipment_providers.calculate_timeout_use_case_provider,
        ),
        chat_moderation=moderation_service,
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    roll_command_handler = RollCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_roll,
        handle_roll_use_case=HandleRollUseCase(
            unit_of_work_factory=uow_factories.build_roll_uow_factory(),
            roll_cooldown_use_case_provider=providers.equipment_providers.roll_cooldown_use_case_provider,
            calculate_timeout_use_case_provider=providers.equipment_providers.calculate_timeout_use_case_provider,
        ),
        chat_moderation=moderation_service,
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    balance_command_handler = BalanceCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_balance,
        handle_balance_use_case=HandleBalanceUseCase(
            unit_of_work_factory=uow_factories.build_balance_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    bonus_command_handler = BonusCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_bonus,
        handle_bonus_use_case=HandleBonusUseCase(
            unit_of_work_factory=uow_factories.build_bonus_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    transfer_command_handler = TransferCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_transfer,
        handle_transfer_use_case=HandleTransferUseCase(
            unit_of_work_factory=uow_factories.build_transfer_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    shop_command_handler = ShopCommandHandler(
        command_prefix=prefix,
        command_shop_name=settings.command_shop,
        command_buy_name=settings.command_buy,
        handle_shop_use_case=HandleShopUseCase(
            unit_of_work_factory=uow_factories.build_shop_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    equipment_command_handler = EquipmentCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_equipment,
        command_shop=settings.command_shop,
        handle_equipment_use_case=HandleEquipmentUseCase(
            unit_of_work_factory=uow_factories.build_equipment_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    top_bottom_command_handler = TopBottomCommandHandler(
        command_prefix=prefix,
        command_top=settings.command_top,
        command_bottom=settings.command_bottom,
        handle_top_bottom_use_case=HandleTopBottomUseCase(
            unit_of_work_factory=uow_factories.build_top_bottom_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    stats_command_handler = StatsCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_stats,
        handle_stats_use_case=HandleStatsUseCase(
            unit_of_work_factory=uow_factories.build_stats_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
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
    help_command_handler = HelpCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_help,
        handle_help_use_case=HandleHelpUseCase(unit_of_work_factory=uow_factories.build_help_uow_factory()),
        commands=commands,
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    guess_command_handler = GuessCommandHandler(
        command_prefix=prefix,
        command_guess=settings.command_guess,
        command_guess_letter=settings.command_guess_letter,
        command_guess_word=settings.command_guess_word,
        handle_guess_use_case=HandleGuessUseCase(
            minigame_service=providers.minigame_providers.minigame_service,
            unit_of_work_factory=uow_factories.build_guess_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )
    rps_command_handler = RpsCommandHandler(
        command_prefix=prefix,
        command_name=settings.command_rps,
        handle_rps_use_case=HandleRpsUseCase(
            minigame_service=providers.minigame_providers.minigame_service,
            unit_of_work_factory=uow_factories.build_rps_uow_factory(),
        ),
        bot_nick=bot.nick,
        post_message_fn=post_message_fn,
    )

    return CommandRegistry(
        followage_command_handler=followage_command_handler,
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
