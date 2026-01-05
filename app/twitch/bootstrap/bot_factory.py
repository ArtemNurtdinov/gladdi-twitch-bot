from app.ai.bootstrap import AIProviders
from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.gen.conversation.infrastructure.conversation_repository import ConversationRepositoryImpl
from app.battle.bootstrap import BattleProviders
from app.betting.bootstrap import BettingProviders
from app.chat.application.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.chat.bootstrap import ChatProviders
from app.chat.data.chat_repository import ChatRepositoryImpl
from app.commands.ask.application.handle_ask_use_case import HandleAskUseCase
from app.commands.ask.infrastructure.ask_uow import SqlAlchemyAskUnitOfWorkFactory
from app.commands.balance.handle_balance_use_case import HandleBalanceUseCase
from app.commands.battle.handle_battle_use_case import HandleBattleUseCase
from app.commands.bonus.handle_bonus_use_case import HandleBonusUseCase
from app.commands.chat.handle_chat_message_use_case import HandleChatMessageUseCase
from app.commands.chat.infrastructure.chat_message_uow import SqlAlchemyChatMessageUnitOfWorkFactory
from app.commands.equipment.handle_equipment_use_case import HandleEquipmentUseCase
from app.commands.follow.application.get_followage_use_case import GetFollowageUseCase
from app.commands.follow.application.handle_followage_use_case import HandleFollowAgeUseCase
from app.commands.follow.infrastructure.follow_age_uow import SqlAlchemyFollowAgeUnitOfWorkFactory
from app.commands.guess.handle_guess_use_case import HandleGuessUseCase
from app.commands.help.handle_help_use_case import HandleHelpUseCase
from app.commands.roll.handle_roll_use_case import HandleRollUseCase
from app.commands.shop.handle_shop_use_case import HandleShopUseCase
from app.commands.stats.handle_stats_use_case import HandleStatsUseCase
from app.commands.top_bottom.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.commands.transfer.handle_transfer_use_case import HandleTransferUseCase
from app.economy.bootstrap import EconomyProviders
from app.equipment.bootstrap import EquipmentProviders
from app.follow.application.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.bootstrap import FollowProviders
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.application.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.bootstrap import JokeProviders
from app.minigame.application.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.handle_rps_use_case import HandleRpsUseCase
from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.minigame.bootstrap import MinigameProviders
from app.stream.application.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.application.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.application.model import RestoreStreamJobDTO
from app.stream.bootstrap import StreamProviders
from app.twitch.bootstrap.bot_settings import BotSettings
from app.twitch.bootstrap.twitch import TwitchProviders
from app.twitch.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.twitch.presentation.background.bot_tasks import BotBackgroundTasks
from app.twitch.presentation.background.jobs.chat_summarizer_job import ChatSummarizerJob
from app.twitch.presentation.background.jobs.minigame_tick_job import MinigameTickJob
from app.twitch.presentation.background.jobs.post_joke_job import PostJokeJob
from app.twitch.presentation.background.jobs.stream_status_job import StreamStatusJob
from app.twitch.presentation.background.jobs.token_checker_job import TokenCheckerJob
from app.twitch.presentation.background.jobs.viewer_time_job import ViewerTimeJob
from app.twitch.presentation.interaction.chat_event_handler import ChatEventHandler
from app.twitch.presentation.interaction.commands.ask import AskCommandHandler
from app.twitch.presentation.interaction.commands.balance import BalanceCommandHandler
from app.twitch.presentation.interaction.commands.battle import BattleCommandHandler
from app.twitch.presentation.interaction.commands.bonus import BonusCommandHandler
from app.twitch.presentation.interaction.commands.equipment import EquipmentCommandHandler
from app.twitch.presentation.interaction.commands.followage import FollowageCommandHandler
from app.twitch.presentation.interaction.commands.guess import GuessCommandHandler
from app.twitch.presentation.interaction.commands.help import HelpCommandHandler
from app.twitch.presentation.interaction.commands.registry import CommandRegistry
from app.twitch.presentation.interaction.commands.roll import RollCommandHandler
from app.twitch.presentation.interaction.commands.rps import RpsCommandHandler
from app.twitch.presentation.interaction.commands.shop import ShopCommandHandler
from app.twitch.presentation.interaction.commands.stats import StatsCommandHandler
from app.twitch.presentation.interaction.commands.top_bottom import TopBottomCommandHandler
from app.twitch.presentation.interaction.commands.transfer import TransferCommandHandler
from app.twitch.presentation.twitch_bot import Bot
from app.user.bootstrap import UserProviders
from app.viewer.application.handle_viewer_time_use_case import HandleViewerTimeUseCase
from app.viewer.bootstrap import ViewerProviders
from core.bootstrap.background import BackgroundProviders
from core.bootstrap.telegram import TelegramProviders
from core.db import SessionLocal, db_ro_session
from core.provider import Provider


class BotFactory:
    def __init__(
        self,
        twitch_providers: TwitchProviders,
        ai_providers: AIProviders,
        chat_providers: ChatProviders,
        follow_providers: FollowProviders,
        joke_providers: JokeProviders,
        user_providers: UserProviders,
        viewer_providers: ViewerProviders,
        stream_providers: StreamProviders,
        economy_providers: EconomyProviders,
        minigame_providers: MinigameProviders,
        equipment_providers: EquipmentProviders,
        battle_providers: BattleProviders,
        betting_providers: BettingProviders,
        background_providers: BackgroundProviders,
        telegram_providers: TelegramProviders,
        settings: BotSettings,
    ):
        self._twitch = twitch_providers
        self._ai = ai_providers
        self._chat = chat_providers
        self._follow = follow_providers
        self._joke = joke_providers
        self._user = user_providers
        self._viewer = viewer_providers
        self._stream = stream_providers
        self._economy = economy_providers
        self._minigame = minigame_providers
        self._equipment = equipment_providers
        self._battle = battle_providers
        self._betting = betting_providers
        self._background = background_providers
        self._telegram = telegram_providers
        self._settings = settings

    def create(self) -> Bot:
        bot = Bot(self._twitch, self._user, self._settings)
        system_prompt = self._ai.prompt_service.get_system_prompt_for_group()
        chat_response_use_case = self._create_chat_response_use_case(system_prompt)

        bot.set_minigame_orchestrator(self._create_minigame(bot, system_prompt))
        bot.set_background_tasks(self._create_background_tasks(bot, chat_response_use_case))
        bot.set_command_registry(self._create_command_registry(bot, chat_response_use_case, system_prompt))
        bot.set_chat_event_handler(self._create_chat_event_handler(bot, chat_response_use_case, system_prompt))
        self._restore_stream_context()
        return bot

    def _create_chat_response_use_case(self, system_prompt: str) -> ChatResponseUseCase:
        return ChatResponseUseCase(
            conversation_service_provider=self._ai.conversation_service_provider,
            llm_client=self._ai.llm_client,
            system_prompt=system_prompt,
            db_readonly_session_provider=lambda: db_ro_session(),
        )

    def _create_minigame(self, bot: Bot, system_prompt: str) -> MinigameOrchestrator:
        return MinigameOrchestrator(
            minigame_service=self._minigame.minigame_service,
            economy_policy_provider=self._economy.economy_policy_provider,
            chat_use_case_provider=self._chat.chat_use_case_provider,
            stream_service_provider=self._stream.stream_service_provider,
            get_used_words_use_case_provider=self._minigame.get_used_words_use_case_provider,
            add_used_words_use_case_provider=self._minigame.add_used_words_use_case_provider,
            llm_client=self._ai.llm_client,
            system_prompt=system_prompt,
            prefix=self._settings.prefix,
            command_guess_letter=self._settings.command_guess_letter,
            command_guess_word=self._settings.command_guess_word,
            command_guess=self._settings.command_guess,
            command_rps=self._settings.command_rps,
            bot_nick_provider=lambda: bot.nick,
            send_channel_message=bot.send_channel_message,
            conversation_service_provider=self._ai.conversation_service_provider,
        )

    def _create_background_tasks(self, bot: Bot, chat_response_use_case: ChatResponseUseCase) -> BotBackgroundTasks:
        return BotBackgroundTasks(
            runner=self._background.background_runner,
            jobs=[
                PostJokeJob(
                    channel_name=self._settings.channel_name,
                    handle_post_joke_use_case=HandlePostJokeUseCase(
                        joke_service=self._joke.joke_service,
                        user_cache=self._user.user_cache,
                        stream_info=self._stream.stream_info_port,
                        chat_response_use_case=chat_response_use_case,
                        conversation_service_provider=self._ai.conversation_service_provider,
                        chat_use_case_provider=self._chat.chat_use_case_provider,
                    ),
                    db_session_provider=SessionLocal.begin,
                    send_channel_message=bot.send_channel_message,
                    bot_nick_provider=lambda: bot.nick,
                ),
                TokenCheckerJob(
                    handle_token_checker_use_case=HandleTokenCheckerUseCase(twitch_auth=self._twitch.twitch_auth, interval_seconds=1000),
                ),
                StreamStatusJob(
                    channel_name=self._settings.channel_name,
                    handle_stream_status_use_case=HandleStreamStatusUseCase(
                        user_cache=self._user.user_cache,
                        stream_status_port=self._stream.stream_status_port,
                        stream_service_provider=self._stream.stream_service_provider,
                        start_stream_use_case_provider=self._stream.start_stream_use_case_provider,
                        viewer_service_provider=self._viewer.viewer_service_provider,
                        battle_use_case_provider=self._battle.battle_use_case_provider,
                        economy_policy_provider=self._economy.economy_policy_provider,
                        chat_use_case_provider=self._chat.chat_use_case_provider,
                        conversation_service_provider=self._ai.conversation_service_provider,
                        minigame_service=self._minigame.minigame_service,
                        telegram_bot=self._telegram.telegram_bot,
                        telegram_group_id=self._settings.group_id,
                        chat_response_use_case=chat_response_use_case,
                        state=bot.chat_summary_state,
                    ),
                    db_session_provider=SessionLocal.begin,
                    db_readonly_session_provider=lambda: db_ro_session(),
                    stream_status_interval_seconds=self._settings.check_stream_status_interval_seconds,
                ),
                ChatSummarizerJob(
                    channel_name=self._settings.channel_name,
                    handle_chat_summarizer_use_case=HandleChatSummarizerUseCase(
                        stream_service_provider=self._stream.stream_service_provider,
                        chat_use_case_provider=self._chat.chat_use_case_provider,
                        chat_response_use_case=chat_response_use_case,
                    ),
                    db_readonly_session_provider=lambda: db_ro_session(),
                    chat_summary_state=bot.chat_summary_state,
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
                        viewer_service_provider=self._viewer.viewer_service_provider,
                        stream_service_provider=self._stream.stream_service_provider,
                        economy_policy_provider=self._economy.economy_policy_provider,
                        user_cache=self._user.user_cache,
                        stream_chatters_port=self._stream.stream_chatters_port,
                    ),
                    db_session_provider=SessionLocal.begin,
                    db_readonly_session_provider=lambda: db_ro_session(),
                    bot_nick_provider=lambda: bot.nick,
                    check_interval_seconds=self._settings.check_viewers_interval_seconds,
                ),
                FollowersSyncJob(
                    channel_name=self._settings.channel_name,
                    handle_followers_sync_use_case=HandleFollowersSyncUseCase(
                        followers_port=self._follow.followers_port,
                        followers_repository_provider=self._follow.followers_repository_provider,
                    ),
                    db_session_provider=SessionLocal.begin,
                    interval_seconds=self._settings.sync_followers_interval_seconds,
                ),
            ],
        )

    def _create_command_registry(self, bot: Bot, chat_response_use_case: ChatResponseUseCase, system_prompt: str) -> CommandRegistry:
        prefix = self._settings.prefix

        def bot_nick_provider() -> str:
            return bot.nick

        post_message_fn = bot.post_message_in_twitch_chat
        timeout_fn = bot.timeout_user
        settings = self._settings
        ask_uow_factory = self._build_ask_uow_factory()

        follow_age = FollowageCommandHandler(
            handle_follow_age_use_case=HandleFollowAgeUseCase(
                chat_repo_provider=Provider(lambda db: ChatRepositoryImpl(db)),
                conversation_repo_provider=Provider(lambda db: ConversationRepositoryImpl(db)),
                get_followage_use_case=GetFollowageUseCase(
                    followage_port=self._follow.followage_port,
                ),
                chat_response_use_case=chat_response_use_case,
                unit_of_work_factory=self._build_follow_age_uow_factory(),
                system_prompt=system_prompt,
            ),
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        ask = AskCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_gladdi,
            handle_ask_use_case=HandleAskUseCase(
                get_intent_from_text_use_case=self._ai.get_intent_use_case,
                prompt_service=self._ai.prompt_service,
                unit_of_work_factory=ask_uow_factory,
                system_prompt=system_prompt,
                chat_response_use_case=chat_response_use_case,
            ),
            post_message_fn=post_message_fn,
            bot_nick_provider=bot_nick_provider,
        )
        battle = BattleCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_fight,
            handle_battle_use_case=HandleBattleUseCase(
                economy_policy_provider=self._economy.economy_policy_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
                conversation_service_provider=self._ai.conversation_service_provider,
                battle_use_case_provider=self._battle.battle_use_case_provider,
                get_user_equipment_use_case_provider=self._equipment.get_user_equipment_use_case_provider,
                chat_response_use_case=chat_response_use_case,
                calculate_timeout_use_case_provider=self._equipment.calculate_timeout_use_case_provider,
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
                economy_policy_provider=self._economy.economy_policy_provider,
                betting_service_provider=self._betting.betting_service_provider,
                roll_cooldown_use_case_provider=self._equipment.roll_cooldown_use_case_provider,
                get_user_equipment_use_case_provider=self._equipment.get_user_equipment_use_case_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
                calculate_timeout_use_case_provider=self._equipment.calculate_timeout_use_case_provider,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            timeout_fn=timeout_fn,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        balance = BalanceCommandHandler(
            handle_balance_use_case=HandleBalanceUseCase(
                economy_policy_provider=self._economy.economy_policy_provider, chat_use_case_provider=self._chat.chat_use_case_provider
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        bonus = BonusCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_bonus,
            handle_bonus_use_case=HandleBonusUseCase(
                stream_service_provider=self._stream.stream_service_provider,
                get_user_equipment_use_case_provider=self._equipment.get_user_equipment_use_case_provider,
                economy_policy_provider=self._economy.economy_policy_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
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
                economy_policy_provider=self._economy.economy_policy_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
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
                economy_policy_provider=self._economy.economy_policy_provider,
                add_equipment_use_case_provider=self._equipment.add_equipment_use_case_provider,
                equipment_exists_use_case_provider=self._equipment.equipment_exists_use_case_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
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
                get_user_equipment_use_case_provider=self._equipment.get_user_equipment_use_case_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
            ),
            db_session_provider=SessionLocal.begin,
            db_readonly_session_provider=lambda: db_ro_session(),
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        top_bottom = TopBottomCommandHandler(
            handle_top_bottom_use_case=HandleTopBottomUseCase(
                economy_policy_provider=self._economy.economy_policy_provider, chat_use_case_provider=self._chat.chat_use_case_provider
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
                economy_policy_provider=self._economy.economy_policy_provider,
                betting_service_provider=self._betting.betting_service_provider,
                battle_use_case_provider=self._battle.battle_use_case_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
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
            handle_help_use_case=HandleHelpUseCase(chat_use_case_provider=self._chat.chat_use_case_provider),
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
                minigame_service=self._minigame.minigame_service,
                economy_policy_provider=self._economy.economy_policy_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )
        rps = RpsCommandHandler(
            handle_rps_use_case=HandleRpsUseCase(
                minigame_service=self._minigame.minigame_service,
                economy_policy_provider=self._economy.economy_policy_provider,
                chat_use_case_provider=self._chat.chat_use_case_provider,
            ),
            db_session_provider=SessionLocal.begin,
            bot_nick_provider=bot_nick_provider,
            post_message_fn=post_message_fn,
        )

        return CommandRegistry(
            followage=follow_age,
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

    def _create_chat_event_handler(self, bot: Bot, chat_response_use_case: ChatResponseUseCase, system_prompt: str) -> ChatEventHandler:
        chat_message_uow_factory = self._build_chat_message_uow_factory()
        handle_chat_message = HandleChatMessageUseCase(
            unit_of_work_factory=chat_message_uow_factory,
            get_intent_from_text_use_case=self._ai.get_intent_use_case,
            prompt_service=self._ai.prompt_service,
            system_prompt=system_prompt,
            chat_response_use_case=chat_response_use_case,
        )
        return ChatEventHandler(
            handle_chat_message_use_case=handle_chat_message,
            send_channel_message=bot.send_channel_message,
        )

    def _restore_stream_context(self):
        if not self._settings.channel_name:
            return

        restore_stream_job_dto = RestoreStreamJobDTO(self._settings.channel_name)

        HandleRestoreStreamContextUseCase(
            stream_service_provider=self._stream.stream_service_provider,
            minigame_service=self._minigame.minigame_service,
            db_readonly_session_provider=lambda: db_ro_session(),
        ).handle(restore_stream_job_dto)

    def _build_ask_uow_factory(self) -> SqlAlchemyAskUnitOfWorkFactory:
        return SqlAlchemyAskUnitOfWorkFactory(
            session_factory_rw=SessionLocal.begin,
            session_factory_ro=db_ro_session,
            chat_repo_provider=self._chat.chat_repo_provider,
            conversation_repo_provider=self._ai.conversation_repo_provider,
        )

    def _build_chat_message_uow_factory(self) -> SqlAlchemyChatMessageUnitOfWorkFactory:
        return SqlAlchemyChatMessageUnitOfWorkFactory(
            session_factory_rw=SessionLocal.begin,
            session_factory_ro=db_ro_session,
            chat_repo_provider=self._chat.chat_repo_provider,
            economy_policy_provider=self._economy.economy_policy_provider,
            stream_repo_provider=self._stream.stream_repo_provider,
            viewer_repo_provider=self._viewer.viewer_repo_provider,
            conversation_repo_provider=self._ai.conversation_repo_provider,
        )

    def _build_follow_age_uow_factory(self) -> SqlAlchemyFollowAgeUnitOfWorkFactory:
        return SqlAlchemyFollowAgeUnitOfWorkFactory(
            session_factory_rw=SessionLocal.begin,
            session_factory_ro=db_ro_session,
            chat_repo_provider=self._chat.chat_repo_provider,
            conversation_repo_provider=self._ai.conversation_repo_provider,
        )
