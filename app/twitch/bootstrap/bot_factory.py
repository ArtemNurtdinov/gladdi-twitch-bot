from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.twitch.application.background.chat_summary.handle_chat_summarizer_use_case import (
    HandleChatSummarizerUseCase,
)
from app.twitch.application.background.minigame_tick.handle_minigame_tick_use_case import (
    HandleMinigameTickUseCase,
)
from app.twitch.application.background.post_joke.handle_post_joke_use_case import HandlePostJokeUseCase
from app.twitch.application.background.stream_status.handle_stream_status_use_case import (
    HandleStreamStatusUseCase,
)
from app.twitch.application.background.token_checker.handle_token_checker_use_case import (
    HandleTokenCheckerUseCase,
)
from app.twitch.application.background.viewer_time.handle_viewer_time_use_case import HandleViewerTimeUseCase
from app.twitch.application.interaction.ask.handle_ask_use_case import HandleAskUseCase
from app.twitch.application.interaction.balance.handle_balance_use_case import HandleBalanceUseCase
from app.twitch.application.interaction.battle.handle_battle_use_case import HandleBattleUseCase
from app.twitch.application.interaction.bonus.handle_bonus_use_case import HandleBonusUseCase
from app.twitch.application.interaction.chat.handle_chat_message_use_case import HandleChatMessageUseCase
from app.twitch.application.interaction.equipment.handle_equipment_use_case import HandleEquipmentUseCase
from app.twitch.application.interaction.follow.handle_followage_use_case import HandleFollowageUseCase
from app.twitch.application.interaction.guess.handle_guess_use_case import HandleGuessUseCase
from app.twitch.application.interaction.help.handle_help_use_case import HandleHelpUseCase
from app.twitch.application.interaction.rps.handle_rps_use_case import HandleRpsUseCase
from app.twitch.application.interaction.roll.handle_roll_use_case import HandleRollUseCase
from app.twitch.application.interaction.shop.handle_shop_use_case import HandleShopUseCase
from app.twitch.application.interaction.stats.handle_stats_use_case import HandleStatsUseCase
from app.twitch.application.interaction.top_bottom.handle_top_bottom_use_case import (
    HandleTopBottomUseCase,
)
from app.twitch.application.interaction.transfer.handle_transfer_use_case import HandleTransferUseCase
from app.twitch.bootstrap.deps import BotDependencies
from app.twitch.bootstrap.twitch_bot_settings import TwitchBotSettings
from app.twitch.presentation.background.bot_tasks import BotBackgroundTasks
from app.twitch.presentation.background.jobs.chat_summarizer_job import ChatSummarizerJob
from app.twitch.presentation.background.jobs.minigame_tick_job import MinigameTickJob
from app.twitch.presentation.background.jobs.post_joke_job import PostJokeJob
from app.twitch.presentation.background.jobs.stream_status_job import StreamStatusJob
from app.twitch.presentation.background.jobs.token_checker_job import TokenCheckerJob
from app.twitch.presentation.background.jobs.viewer_time_job import ViewerTimeJob
from app.twitch.presentation.interaction.chat_event_handler import ChatEventHandler
from app.twitch.presentation.interaction.commands.registry import CommandRegistry
from app.twitch.presentation.interaction.commands.ask import AskCommandHandler
from app.twitch.presentation.interaction.commands.battle import BattleCommandHandler
from app.twitch.presentation.interaction.commands.balance import BalanceCommandHandler
from app.twitch.presentation.interaction.commands.bonus import BonusCommandHandler
from app.twitch.presentation.interaction.commands.equipment import EquipmentCommandHandler
from app.twitch.presentation.interaction.commands.followage import FollowageCommandHandler
from app.twitch.presentation.interaction.commands.guess import GuessCommandHandler
from app.twitch.presentation.interaction.commands.help import HelpCommandHandler
from app.twitch.presentation.interaction.commands.roll import RollCommandHandler
from app.twitch.presentation.interaction.commands.rps import RpsCommandHandler
from app.twitch.presentation.interaction.commands.shop import ShopCommandHandler
from app.twitch.presentation.interaction.commands.stats import StatsCommandHandler
from app.twitch.presentation.interaction.commands.top_bottom import TopBottomCommandHandler
from app.twitch.presentation.interaction.commands.transfer import TransferCommandHandler
from app.twitch.presentation.twitch_bot import Bot
from core.db import SessionLocal, db_ro_session


class BotFactory:
    def __init__(self, deps: BotDependencies, settings: TwitchBotSettings):
        self._deps = deps
        self._settings = settings

    def create(self) -> Bot:
        bot = Bot(self._deps, self._settings)

        bot.set_minigame_orchestrator(self._create_minigame(bot))
        bot.set_background_tasks(self._create_background_tasks(bot))
        bot.set_command_registry(self._create_command_registry(bot))
        bot.set_chat_event_handler(self._create_chat_event_handler(bot))
        bot.restore_stream_context()
        return bot

    def _create_minigame(self, bot: Bot) -> MinigameOrchestrator:
        return MinigameOrchestrator(
            minigame_service=self._deps.minigame_service,
            economy_service_factory=self._deps.economy_service,
            chat_use_case_factory=self._deps.chat_use_case,
            stream_service_factory=self._deps.stream_service,
            get_used_words_use_case_factory=self._deps.get_used_words_use_case,
            add_used_word_use_case_factory=self._deps.add_used_word_use_case,
            ai_conversation_use_case_factory=self._deps.ai_conversation_use_case,
            llm_client=self._deps.llm_client,
            system_prompt=bot.SYSTEM_PROMPT_FOR_GROUP,
            prefix=self._settings.prefix,
            command_guess_letter=self._settings.command_guess_letter,
            command_guess_word=self._settings.command_guess_word,
            command_guess=self._settings.command_guess,
            command_rps=self._settings.command_rps,
            bot_nick_provider=lambda: bot.nick,
            send_channel_message=bot.send_channel_message,
        )

    def _create_background_tasks(self, bot: Bot) -> BotBackgroundTasks:
        return BotBackgroundTasks(
            runner=self._deps.background_runner,
            jobs=[
                PostJokeJob(
                    channel_name=self._settings.channel_name,
                    handle_post_joke_use_case=HandlePostJokeUseCase(
                        joke_service=self._deps.joke_service,
                        user_cache=self._deps.user_cache,
                        twitch_api_service=self._deps.twitch_api_service,
                        generate_response_fn=bot.generate_response_in_chat,
                        ai_conversation_use_case_factory=self._deps.ai_conversation_use_case,
                        chat_use_case_factory=self._deps.chat_use_case,
                    ),
                    db_session_provider=SessionLocal.begin,
                    send_channel_message=bot.send_channel_message,
                    bot_nick_provider=lambda: bot.nick,
                ),
                TokenCheckerJob(
                    handle_token_checker_use_case=HandleTokenCheckerUseCase(
                        twitch_auth=self._deps.twitch_auth,
                        interval_seconds=1000,
                    ),
                ),
                StreamStatusJob(
                    channel_name=self._settings.channel_name,
                    handle_stream_status_use_case=HandleStreamStatusUseCase(
                        user_cache=self._deps.user_cache,
                        twitch_api_service=self._deps.twitch_api_service,
                        stream_service_factory=self._deps.stream_service,
                        start_new_stream_use_case_factory=self._deps.start_new_stream_use_case,
                        viewer_service_factory=self._deps.viewer_service,
                        battle_use_case_factory=self._deps.battle_use_case,
                        economy_service_factory=self._deps.economy_service,
                        chat_use_case_factory=self._deps.chat_use_case,
                        ai_conversation_use_case_factory=self._deps.ai_conversation_use_case,
                        minigame_service=self._deps.minigame_service,
                        telegram_bot=self._deps.telegram_bot,
                        telegram_group_id=self._settings.group_id,
                        generate_response_fn=bot.generate_response_in_chat,
                        state=bot.chat_summary_state,
                    ),
                    db_session_provider=SessionLocal.begin,
                    db_readonly_session_provider=lambda: db_ro_session(),
                    state=bot.chat_summary_state,
                    stream_status_interval_seconds=self._settings.check_stream_status_interval_seconds,
                ),
                ChatSummarizerJob(
                    channel_name=self._settings.channel_name,
                    twitch_api_service=self._deps.twitch_api_service,
                    handle_chat_summarizer_use_case=HandleChatSummarizerUseCase(
                        stream_service_factory=self._deps.stream_service,
                        chat_use_case_factory=self._deps.chat_use_case,
                        generate_response_fn=bot.generate_response_in_chat,
                    ),
                    db_readonly_session_provider=lambda: db_ro_session(),
                    state=bot.chat_summary_state,
                ),
                MinigameTickJob(
                    channel_name=self._settings.channel_name,
                    handle_minigame_tick_use_case=HandleMinigameTickUseCase(
                        minigame_orchestrator=bot.minigame_orchestrator,
                    ),
                ),
                ViewerTimeJob(
                    channel_name=self._settings.channel_name,
                    handle_viewer_time_use_case=HandleViewerTimeUseCase(
                        viewer_service_factory=self._deps.viewer_service,
                        stream_service_factory=self._deps.stream_service,
                        economy_service_factory=self._deps.economy_service,
                        user_cache=self._deps.user_cache,
                        twitch_api_service=self._deps.twitch_api_service,
                    ),
                    db_session_provider=SessionLocal.begin,
                    db_readonly_session_provider=lambda: db_ro_session(),
                    bot_nick_provider=lambda: bot.nick,
                    check_interval_seconds=self._settings.check_viewers_interval_seconds,
                ),
            ],
        )

    def _create_command_registry(self, bot: Bot) -> CommandRegistry:
        prefix = self._settings.prefix
        bot_nick_provider = lambda: bot.nick
        post_message_fn = bot.post_message_in_twitch_chat
        generate_response_fn = bot.generate_response_in_chat
        timeout_fn = bot.timeout_user
        deps = self._deps
        settings = self._settings

        followage = FollowageCommandHandler(
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
        ask = AskCommandHandler(
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
        battle = BattleCommandHandler(
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
        roll = RollCommandHandler(
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
        balance = BalanceCommandHandler(
            handle_balance_use_case=HandleBalanceUseCase(
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        bonus = BonusCommandHandler(
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
        transfer = TransferCommandHandler(
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
        shop = ShopCommandHandler(
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
        equipment = EquipmentCommandHandler(
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
        top_bottom = TopBottomCommandHandler(
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
        stats = StatsCommandHandler(
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
        help_handler = HelpCommandHandler(
            command_prefix=prefix,
            handle_help_use_case=HandleHelpUseCase(
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            commands=commands,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        guess = GuessCommandHandler(
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
        rps = RpsCommandHandler(
            handle_rps_use_case=HandleRpsUseCase(
                minigame_service=deps.minigame_service,
                economy_service_factory=deps.economy_service,
                chat_use_case_factory=deps.chat_use_case,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )

        return CommandRegistry(
            followage=followage,
            ask=ask,
            battle=battle,
            roll=roll,
            balance=balance,
            bonus=bonus,
            transfer=transfer,
            shop=shop,
            equipment=equipment,
            top_bottom=top_bottom,
            stats=stats,
            help=help_handler,
            guess=guess,
            rps=rps,
        )

    def _create_chat_event_handler(self, bot: Bot) -> ChatEventHandler:
        handle_chat_message = HandleChatMessageUseCase(
            chat_use_case_factory=self._deps.chat_use_case,
            economy_service_factory=self._deps.economy_service,
            stream_service_factory=self._deps.stream_service,
            viewer_service_factory=self._deps.viewer_service,
            intent_use_case=self._deps.intent_use_case,
            prompt_service=self._deps.prompt_service,
            generate_response_fn=bot.generate_response_in_chat,
        )
        return ChatEventHandler(
            handle_chat_message_use_case=handle_chat_message,
            db_session_provider=SessionLocal.begin,
            send_channel_message=bot.send_channel_message,
        )

