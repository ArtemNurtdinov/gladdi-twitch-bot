from typing import Callable, Awaitable

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
            chat_use_case_factory=deps.chat_use_case,
            ai_conversation_use_case_factory=deps.ai_conversation_use_case,
            command_name=settings.command_followage,
            bot_nick_provider=bot_nick_provider,
            generate_response_fn=generate_response_fn,
            twitch_api_service=deps.twitch_api_service,
            post_message_fn=post_message_fn,
        )
        self.ask = AskCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_gladdi,
            intent_use_case=deps.intent_use_case,
            prompt_service=deps.prompt_service,
            ai_conversation_use_case_factory=deps.ai_conversation_use_case,
            chat_use_case_factory=deps.chat_use_case,
            generate_response_fn=generate_response_fn,
            post_message_fn=post_message_fn,
            bot_nick_provider=bot_nick_provider,
        )
        self.battle = BattleCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_fight,
            economy_service_factory=deps.economy_service,
            chat_use_case_factory=deps.chat_use_case,
            ai_conversation_use_case_factory=deps.ai_conversation_use_case,
            battle_use_case_factory=deps.battle_use_case,
            equipment_service_factory=deps.equipment_service,
            timeout_fn=timeout_fn,
            generate_response_fn=generate_response_fn,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.roll = RollCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_roll,
            economy_service_factory=deps.economy_service,
            betting_service_factory=deps.betting_service,
            equipment_service_factory=deps.equipment_service,
            chat_use_case_factory=deps.chat_use_case,
            timeout_fn=timeout_fn,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.balance = BalanceCommandHandler(
            economy_service_factory=deps.economy_service,
            chat_use_case_factory=deps.chat_use_case,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.bonus = BonusCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_bonus,
            stream_service_factory=deps.stream_service,
            equipment_service_factory=deps.equipment_service,
            economy_service_factory=deps.economy_service,
            chat_use_case_factory=deps.chat_use_case,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.transfer = TransferCommandHandler(
            command_prefix=prefix,
            economy_service_factory=deps.economy_service,
            chat_use_case_factory=deps.chat_use_case,
            command_name=settings.command_transfer,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.shop = ShopCommandHandler(
            command_prefix=prefix,
            command_shop_name=settings.command_shop,
            command_buy_name=settings.command_buy,
            economy_service_factory=deps.economy_service,
            equipment_service_factory=deps.equipment_service,
            chat_use_case_factory=deps.chat_use_case,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.equipment = EquipmentCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_equipment,
            command_shop=settings.command_shop,
            equipment_service_factory=deps.equipment_service,
            chat_use_case_factory=deps.chat_use_case,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.top_bottom = TopBottomCommandHandler(
            economy_service_factory=deps.economy_service,
            chat_use_case_factory=deps.chat_use_case,
            command_top=settings.command_top,
            command_bottom=settings.command_bottom,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.stats = StatsCommandHandler(
            economy_service_factory=deps.economy_service,
            betting_service_factory=deps.betting_service,
            battle_use_case_factory=deps.battle_use_case,
            chat_use_case_factory=deps.chat_use_case,
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
            chat_use_case_factory=deps.chat_use_case,
            commands=commands,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.guess = GuessCommandHandler(
            command_prefix=prefix,
            command_guess=settings.command_guess,
            command_guess_letter=settings.command_guess_letter,
            command_guess_word=settings.command_guess_word,
            minigame_service=deps.minigame_service,
            economy_service_factory=deps.economy_service,
            chat_use_case_factory=deps.chat_use_case,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        self.rps = RpsCommandHandler(
            minigame_service=deps.minigame_service,
            economy_service_factory=deps.economy_service,
            chat_use_case_factory=deps.chat_use_case,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )

