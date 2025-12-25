from typing import Callable, Awaitable

from app.twitch.application.interaction.ask.handle_ask_use_case import HandleAskUseCase
from app.twitch.application.interaction.balance.handle_balance_use_case import HandleBalanceUseCase
from app.twitch.application.interaction.battle.handle_battle_use_case import HandleBattleUseCase
from app.twitch.application.interaction.bonus.handle_bonus_use_case import HandleBonusUseCase
from app.twitch.application.interaction.equipment.handle_equipment_use_case import HandleEquipmentUseCase
from app.twitch.application.interaction.follow.handle_followage_use_case import HandleFollowageUseCase
from app.twitch.application.interaction.guess.handle_guess_use_case import HandleGuessUseCase
from app.twitch.application.interaction.help.handle_help_use_case import HandleHelpUseCase
from app.twitch.application.interaction.rps.handle_rps_use_case import HandleRpsUseCase
from app.twitch.application.interaction.roll.handle_roll_use_case import HandleRollUseCase
from app.twitch.application.interaction.top_bottom.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.twitch.application.interaction.stats.handle_stats_use_case import HandleStatsUseCase
from app.twitch.application.interaction.transfer.handle_transfer_use_case import HandleTransferUseCase
from app.twitch.application.interaction.shop.handle_shop_use_case import HandleShopUseCase
from app.twitch.bootstrap.deps import BotDependencies
from app.twitch.bootstrap.twitch_bot_settings import TwitchBotSettings
from app.twitch.presentation.commands.ask import AskCommandHandler
from app.twitch.presentation.commands.battle import BattleCommandHandler
from app.twitch.presentation.commands.balance import BalanceCommandHandler
from app.twitch.presentation.commands.bonus import BonusCommandHandler
from app.twitch.presentation.commands.equipment import EquipmentCommandHandler
from app.twitch.presentation.commands.followage import FollowageCommandHandler
from app.twitch.presentation.commands.guess import GuessCommandHandler
from app.twitch.presentation.commands.help import HelpCommandHandler
from app.twitch.presentation.commands.roll import RollCommandHandler
from app.twitch.presentation.commands.rps import RpsCommandHandler
from app.twitch.presentation.commands.shop import ShopCommandHandler
from app.twitch.presentation.commands.stats import StatsCommandHandler
from app.twitch.presentation.commands.top_bottom import TopBottomCommandHandler
from app.twitch.presentation.commands.transfer import TransferCommandHandler
from core.db import SessionLocal, db_ro_session


class CommandRegistry:
    def __init__(
        self,
        deps: BotDependencies,
        settings: TwitchBotSettings,
        prefix: str,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, object], Awaitable[None]],
        generate_response_fn: Callable[[str, str], str],
        timeout_fn: Callable[[str, str, int, str], Awaitable[None]]
    ):
        self.followage = FollowageCommandHandler(
            handle_followage_use_case=HandleFollowageUseCase(
                chat_use_case_factory=deps.chat_use_case,
                ai_conversation_use_case_factory=deps.ai_conversation_use_case,
                twitch_api_service=deps.twitch_api_service,
                prompt_service=deps.prompt_service,
                generate_response_fn=generate_response_fn,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.ask = AskCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_gladdi,
            handle_ask_use_case=HandleAskUseCase(
                intent_use_case=deps.intent_use_case,
                prompt_service=deps.prompt_service,
                ai_conversation_use_case_factory=deps.ai_conversation_use_case,
                chat_use_case_factory=deps.chat_use_case,
                generate_response_fn=generate_response_fn,
            ),
            db_session_provider=SessionLocal.begin,
            post_message_fn=post_message_fn,
            bot_nick_provider=bot_nick_provider,
        )
        self.battle = BattleCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_fight,
            handle_battle_use_case=HandleBattleUseCase(
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
                ai_conversation_use_case_factory=deps.ai_conversation_use_case,
                battle_use_case_factory=deps.battle_use_case,
                equipment_service_factory=deps.equipment_service,
                generate_response_fn=generate_response_fn,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            timeout_fn=timeout_fn,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.roll = RollCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_roll,
            handle_roll_use_case=HandleRollUseCase(
                economy_service_factory=deps.economy_service,
                betting_service_factory=deps.betting_service,
                equipment_service_factory=deps.equipment_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            timeout_fn=timeout_fn,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.balance = BalanceCommandHandler(
            handle_balance_use_case=HandleBalanceUseCase(
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.bonus = BonusCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_bonus,
            handle_bonus_use_case=HandleBonusUseCase(
                stream_service_factory=deps.stream_service,
                equipment_service_factory=deps.equipment_service,
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.transfer = TransferCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_transfer,
            handle_transfer_use_case=HandleTransferUseCase(
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.shop = ShopCommandHandler(
            command_prefix=prefix,
            command_shop_name=settings.command_shop,
            command_buy_name=settings.command_buy,
            handle_shop_use_case=HandleShopUseCase(
                economy_service_factory=deps.economy_service,
                equipment_service_factory=deps.equipment_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.equipment = EquipmentCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_equipment,
            command_shop=settings.command_shop,
            handle_equipment_use_case=HandleEquipmentUseCase(
                equipment_service_factory=deps.equipment_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.top_bottom = TopBottomCommandHandler(
            handle_top_bottom_use_case=HandleTopBottomUseCase(
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            command_top=settings.command_top,
            command_bottom=settings.command_bottom,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.stats = StatsCommandHandler(
            handle_stats_use_case=HandleStatsUseCase(
                economy_service_factory=deps.economy_service,
                betting_service_factory=deps.betting_service,
                battle_use_case_factory=deps.battle_use_case,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            command_name=settings.command_stats,
            bot_nick_provider=bot_nick_provider,
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
        self.help = HelpCommandHandler(
            command_prefix=prefix,
            handle_help_use_case=HandleHelpUseCase(
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            commands=commands,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.guess = GuessCommandHandler(
            command_prefix=prefix,
            command_guess=settings.command_guess,
            command_guess_letter=settings.command_guess_letter,
            command_guess_word=settings.command_guess_word,
            handle_guess_use_case=HandleGuessUseCase(
                minigame_service=deps.minigame_service,
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.rps = RpsCommandHandler(
            handle_rps_use_case=HandleRpsUseCase(
                minigame_service=deps.minigame_service,
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )

