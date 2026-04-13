import asyncio
from datetime import UTC, datetime

from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.di.container import AIContainer
from app.battle.di.container import BattleContainer
from app.betting.di.container import BettingContainer
from app.bot.domain.model.bot_settings import BotSettings
from app.bot.domain.model.status import BotStatus
from app.bot.presentation.api.model.response.action import BotActionResultResponse
from app.bot.presentation.api.model.response.status import BotStatusResponse
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.di.container import ChatContainer
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.core.di.application_container import app_container
from app.core.logger.domain.logger import Logger
from app.core.network.api.client import ApiClient
from app.economy.di.container import EconomyContainer
from app.equipment.di.container import EquipmentContainer
from app.follow.application.usecases.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.di.container import FollowContainer
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.di.container import JokeContainer
from app.minigame.application.job.minigame_tick_job import MinigameTickJob
from app.minigame.application.use_case.finish_expired_games_use_case import FinishExpiredGamesUseCase
from app.minigame.application.use_case.finish_rps_use_case import FinishRpsUseCase
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.use_case.handle_rps_use_case import HandleRpsUseCase
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.minigame.di.container import MinigameContainer
from app.moderation.application.moderation_service import ModerationService
from app.notification.di.dependencies import provide_notification_repository, provide_telegram_bot
from app.platform.auth.application.job.token_checker_job import TokenCheckerJob
from app.platform.auth.di.container import PlatformAuthContainer
from app.platform.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.platform.chat.application.handle_reply_use_case import HandleReplyUseCase
from app.platform.chat.application.platform_chat_client import PlatformChatClient
from app.platform.chat.infrastructure.twitch_chat_client import TwitchChatClient
from app.platform.command.application.command_router import CommandRouterImpl
from app.platform.command.ask.application.ask_command_handler import AskCommandHandlerImpl
from app.platform.command.ask.application.handle_ask_use_case import HandleAskUseCase
from app.platform.command.ask.di.container import AskContainer
from app.platform.command.balance.application.balance_command_handler import BalanceCommandHandlerImpl
from app.platform.command.balance.application.handle_balance_use_case import HandleBalanceUseCase
from app.platform.command.battle.application.battle_command_handler import BattleCommandHandlerImpl
from app.platform.command.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.platform.command.bonus.application.bonus_command_handler import BonusCommandHandlerImpl
from app.platform.command.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.domain.command_router import CommandRouter
from app.platform.command.equipment.application.equipment_command_handler import EquipmentCommandHandlerImpl
from app.platform.command.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.platform.command.followage.application.followage_command_handler import FollowageCommandHandlerImpl
from app.platform.command.followage.application.usecase.handle_followage_use_case import HandleFollowAgeUseCase
from app.platform.command.guess.application.guess_letter_command_handler import GuessLetterCommandHandlerImpl
from app.platform.command.guess.application.guess_number_command_handler import GuessNumberCommandHandlerImpl
from app.platform.command.guess.application.guess_word_command_handler import GuessWordCommandHandlerImpl
from app.platform.command.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.platform.command.guess.application.rps_command_handler import RpsCommandHandlerImpl
from app.platform.command.help.application.handle_help_use_case import HandleHelpUseCase
from app.platform.command.help.infrastructure.help_command_handler import HelpCommandHandlerImpl
from app.platform.command.roll.application.handle_roll_use_case import HandleRollUseCase
from app.platform.command.roll.application.roll_command_handler import RollCommandHandlerImpl
from app.platform.command.shop.application.buy_command_handler import BuyCommandHandlerImpl
from app.platform.command.shop.application.handle_shop_use_case import HandleShopUseCase
from app.platform.command.shop.application.shop_command_handler import ShopCommandHandlerImpl
from app.platform.command.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.platform.command.stats.application.stats_command_handler import StatsCommandHandlerImpl
from app.platform.command.top_bottom.application.bottom_command_handler import BottomCommandHandlerImpl
from app.platform.command.top_bottom.application.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.platform.command.top_bottom.application.top_command_handler import TopCommandHandlerImpl
from app.platform.command.transfer.application.handle_transfer_use_case import HandleTransferUseCase
from app.platform.command.transfer.application.transfer_command_handler import TransferCommandHandlerImpl
from app.platform.domain.repository import PlatformRepository
from app.platform.infrastructure.api.client import TwitchHelixClient
from app.platform.infrastructure.repository import PlatformRepositoryImpl
from app.shop.di.container import ShopContainer
from app.stream.application.job.stream_status_job import StreamStatusJob
from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.di.container import StreamContainer, get_stream_status_job
from app.task.domain.model.task import Task
from app.task.domain.runner import TaskRunner
from app.task.infrastructure.runner import BackgroundTaskRunner
from app.viewer.di.container import ViewerContainer
from app.viewer.session.application.job.viewer_time_job import ViewerTimeJob
from app.viewer.session.application.usecase.reward_viewer_time_use_case import RewardViewerTimeUseCase
from bootstrap.uow_composition import create_uow_factories
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


class BotManager:
    def __init__(self, settings: BotSettings, logger: Logger):
        self._settings = settings
        self._logger = logger.create_child(__name__)

        self._status: BotStatus = BotStatus.STOPPED
        self._started_at: datetime | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()

        self._api_client: ApiClient | None = None
        self._chat_client: PlatformChatClient | None = None
        self._task_runner: TaskRunner | None = None

        self._task: asyncio.Task | None = None

    def _reset_state(self):
        self._task_runner = None
        self._chat_client = None
        self._task = None
        self._started_at = None

    def _on_bot_done(self, task: asyncio.Task) -> None:
        try:
            exc = task.exception()
            if exc:
                self._last_error = str(exc)
                self._logger.log_error(f"Twitch бот завершился с ошибкой: {exc}")
            else:
                self._logger.log_info("Twitch бот остановлен")
        except asyncio.CancelledError:
            self._logger.log_info("Задача Twitch бота отменена")
        finally:
            self._reset_state()

    def get_status(self) -> BotStatusResponse:
        started_at = self._started_at.isoformat() if self._started_at else None
        return BotStatusResponse(status=self._status, started_at=started_at, last_error=self._last_error)

    async def start_bot(
        self,
        access_token: str,
        refresh_token: str,
        tg_bot_token: str,
        llmbox_host: str,
        intent_detector_host: str,
        client_id: str,
        client_secret: str,
        channel_name: str,
        logger: Logger,
    ) -> BotActionResultResponse:
        async with self._lock:
            if self._task and not self._task.done():
                return BotActionResultResponse(**self.get_status().model_dump(), message="Бот уже запущен")

            platform_auth_container = PlatformAuthContainer(access_token, refresh_token, client_id, client_secret, logger)

            self._api_client: ApiClient = TwitchHelixClient(platform_auth_container.platform_auth)
            platform_repository: PlatformRepository = PlatformRepositoryImpl(self._api_client, self._logger)

            viewer_container = ViewerContainer()
            ai_container = AIContainer(llmbox_host=llmbox_host, intent_detector_host=intent_detector_host)
            ask_container = AskContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
            joke_container = JokeContainer(app_container.logger)
            stream_container = StreamContainer()
            follow_container = FollowContainer()
            economy_container = EconomyContainer()
            equipment_container = EquipmentContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
            shop_container = ShopContainer()
            minigame_container = MinigameContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session, logger=logger)
            battle_container = BattleContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
            betting_container = BettingContainer()
            chat_container = ChatContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)

            uow_factories = create_uow_factories(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                chat_repository_provider=Provider(lambda session: ChatRepositoryImpl(session)),
                chat_use_case=chat_container.chat_use_case(),
                platform_repository=platform_repository,
                system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
                conversation_service_provider=ai_container.conversation_service_provider,
                stream_repository_provider=stream_container.stream_repository_provider,
                follow_repository_provider=follow_container.followers_repository_provider,
                viewer_repository_provider=viewer_container.viewer_repository_provider,
                economy_policy_provider=economy_container.economy_policy_provider,
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                equipment_exists_use_case=equipment_container.equipment_exists_use_case(),
                add_equipment_use_case=equipment_container.add_equipment_use_case(),
                shop_item_repository_provider=shop_container.shop_item_repository_provider,
                get_used_words_use_case=minigame_container.get_used_words_use_case(),
                add_used_word_use_case=minigame_container.add_used_word_use_case(),
                battle_use_case=battle_container.battle_use_case(),
                betting_service_provider=betting_container.betting_service_provider,
            )

            bot_user = await platform_repository.get_authenticated_user()
            if not bot_user:
                raise ValueError("Не удалось получить профиль бота по токену (GET /users). Проверьте авторизацию.")
            bot_name = bot_user.display_name.lower()
            bot_user_id = bot_user.id
            battle_waiting_user = {"value": None}
            chat_summary_state = ChatSummaryState()

            generate_response_use_case = GenerateResponseUseCase(
                chat_response_uow_factory=ai_container.chat_response_uow_factory(),
                llm_repository=ai_container.llm_repository,
                system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
                db_ro_session=db_ro_session,
            )

            moderation_service = ModerationService(
                platform_repository=platform_repository, user_cache=viewer_container.viewer_cache(platform_repository), logger=logger
            )

            followage_command_handler: CommandHandler = FollowageCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_followage,
                handle_follow_age_use_case=HandleFollowAgeUseCase(
                    chat_response_use_case=generate_response_use_case,
                    follow_age_uow_factory=uow_factories.build_follow_age_uow_factory(),
                ),
                bot_nick=bot_name,
            )

            ask_ouw_factory = ask_container.ask_uow_factory(
                chat_repository_provider=Provider(lambda session: ChatRepositoryImpl(session)),
                conversation_service_provider=ai_container.conversation_service_provider,
                system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
            )

            ask_command_handler: CommandHandler = AskCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_gladdi,
                handle_ask_use_case=HandleAskUseCase(
                    get_intent_from_text_use_case=ai_container.get_intent_from_text_use_case(),
                    prompt_service=ai_container.prompt_service,
                    unit_of_work_factory=ask_ouw_factory,
                    chat_response_use_case=generate_response_use_case,
                ),
                bot_nick=bot_name,
            )

            battle_command_handler: CommandHandler = BattleCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_fight,
                handle_battle_use_case=HandleBattleUseCase(
                    battle_uow=uow_factories.build_battle_uow_factory(),
                    chat_response_use_case=generate_response_use_case,
                    calculate_timeout_use_case=equipment_container.calculate_timeout_use_case(),
                ),
                chat_moderation=moderation_service,
                bot_name=bot_name,
                battle_waiting_user=battle_waiting_user,
            )

            roll_command_handler: CommandHandler = RollCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_roll,
                handle_roll_use_case=HandleRollUseCase(
                    unit_of_work_factory=uow_factories.build_roll_uow_factory(),
                    roll_cooldown_use_case=equipment_container.roll_cooldown_use_case(),
                    calculate_timeout_use_case=equipment_container.calculate_timeout_use_case(),
                ),
                chat_moderation=moderation_service,
                bot_name=bot_name,
            )

            balance_command_handler: CommandHandler = BalanceCommandHandlerImpl(
                handle_balance_use_case=HandleBalanceUseCase(
                    balance_uow=uow_factories.build_balance_uow_factory(),
                ),
                bot_name=bot_name,
            )

            bonus_command_handler: CommandHandler = BonusCommandHandlerImpl(
                handle_bonus_use_case=HandleBonusUseCase(
                    bonus_uow=uow_factories.build_bonus_uow_factory(),
                ),
                bot_name=bot_name,
            )

            transfer_command_handler: CommandHandler = TransferCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_transfer,
                handle_transfer_use_case=HandleTransferUseCase(
                    unit_of_work_factory=uow_factories.build_transfer_uow_factory(),
                ),
                bot_nick=bot_name,
            )

            shop_command_handler: CommandHandler = ShopCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_shop_name=self._settings.command_shop,
                command_buy_name=self._settings.command_buy,
                handle_shop_use_case=HandleShopUseCase(
                    shop_uow=uow_factories.build_shop_uow_factory(),
                ),
                bot_nick=bot_name,
            )

            buy_command_handler: CommandHandler = BuyCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_buy_name=self._settings.command_buy,
                handle_shop_use_case=HandleShopUseCase(
                    shop_uow=uow_factories.build_shop_uow_factory(),
                ),
                bot_nick=bot_name,
            )

            equipment_command_handler: CommandHandler = EquipmentCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_shop=self._settings.command_shop,
                handle_equipment_use_case=HandleEquipmentUseCase(
                    unit_of_work_factory=uow_factories.build_equipment_uow_factory(),
                ),
                bot_name=bot_name,
            )

            top_command_handler: CommandHandler = TopCommandHandlerImpl(
                handle_top_bottom_use_case=HandleTopBottomUseCase(
                    unit_of_work_factory=uow_factories.build_top_bottom_uow_factory(),
                ),
                bot_name=bot_name,
            )

            bottom_command_handler: CommandHandler = BottomCommandHandlerImpl(
                handle_top_bottom_use_case=HandleTopBottomUseCase(
                    unit_of_work_factory=uow_factories.build_top_bottom_uow_factory(),
                ),
                bot_name=bot_name,
            )

            commands = {
                self._settings.command_balance,
                self._settings.command_bonus,
                f"{self._settings.command_roll} [сумма]",
                f"{self._settings.command_transfer} @ник сумма",
                self._settings.command_shop,
                f"{self._settings.command_buy} название",
                self._settings.command_equipment,
                self._settings.command_top,
                self._settings.command_bottom,
                self._settings.command_stats,
                self._settings.command_fight,
                f"{self._settings.command_gladdi} текст",
                self._settings.command_followage,
            }

            help_command_handler: CommandHandler = HelpCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                handle_help_use_case=HandleHelpUseCase(unit_of_work_factory=uow_factories.build_help_uow_factory()),
                commands=commands,
                bot_name=bot_name,
            )

            stats_command_handler: CommandHandler = StatsCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_stats,
                handle_stats_use_case=HandleStatsUseCase(
                    stats_uow=uow_factories.build_stats_uow_factory(),
                ),
                bot_name=bot_name,
            )

            guess_number_command_handler: CommandHandler = GuessNumberCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_guess,
                handle_guess_use_case=HandleGuessUseCase(
                    minigame_repository=minigame_container.minigame_repository(),
                    guess_uow=uow_factories.build_guess_uow_factory(),
                ),
                bot_name=bot_name,
            )

            guess_letter_command_handler: CommandHandler = GuessLetterCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_guess_letter,
                handle_guess_use_case=HandleGuessUseCase(
                    minigame_repository=minigame_container.minigame_repository(),
                    guess_uow=uow_factories.build_guess_uow_factory(),
                ),
                bot_name=bot_name,
            )

            guess_word_command_handler: CommandHandler = GuessWordCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_guess_word,
                handle_guess_use_case=HandleGuessUseCase(
                    minigame_repository=minigame_container.minigame_repository(),
                    guess_uow=uow_factories.build_guess_uow_factory(),
                ),
                bot_name=bot_name,
            )

            rps_command_handler: CommandHandler = RpsCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_rps,
                handle_rps_use_case=HandleRpsUseCase(
                    minigame_repository=minigame_container.minigame_repository(),
                    rps_uow=uow_factories.build_rps_uow_factory(),
                ),
                bot_name=bot_name,
            )

            command_router: CommandRouter = CommandRouterImpl(self._settings.prefix)

            command_router.register_command_handler(self._settings.command_followage, followage_command_handler)
            command_router.register_command_handler(self._settings.command_gladdi, ask_command_handler)
            command_router.register_command_handler(self._settings.command_fight, battle_command_handler)
            command_router.register_command_handler(self._settings.command_roll, roll_command_handler)
            command_router.register_command_handler(self._settings.command_balance, balance_command_handler)
            command_router.register_command_handler(self._settings.command_bonus, bonus_command_handler)
            command_router.register_command_handler(self._settings.command_transfer, transfer_command_handler)
            command_router.register_command_handler(self._settings.command_shop, shop_command_handler)
            command_router.register_command_handler(self._settings.command_buy, buy_command_handler)
            command_router.register_command_handler(self._settings.command_equipment, equipment_command_handler)
            command_router.register_command_handler(self._settings.command_top, top_command_handler)
            command_router.register_command_handler(self._settings.command_bottom, bottom_command_handler)
            command_router.register_command_handler(self._settings.command_help, help_command_handler)
            command_router.register_command_handler(self._settings.command_stats, stats_command_handler)
            command_router.register_command_handler(self._settings.command_guess, guess_number_command_handler)
            command_router.register_command_handler(self._settings.command_guess_letter, guess_letter_command_handler)
            command_router.register_command_handler(self._settings.command_guess_word, guess_word_command_handler)
            command_router.register_command_handler(self._settings.command_rps, rps_command_handler)

            handle_chat_message_use_case = HandleChatMessageUseCase(
                unit_of_work_factory=uow_factories.build_chat_message_uow_factory(),
                get_intent_from_text_use_case=ai_container.get_intent_from_text_use_case(),
                prompt_service=ai_container.prompt_service,
                generate_response_use_case=generate_response_use_case,
            )

            handle_reply_use_case = HandleReplyUseCase(
                chat_message_uow=uow_factories.build_chat_message_uow_factory(),
                prompt_service=ai_container.prompt_service,
                generate_response_use_case=generate_response_use_case,
            )

            chat_client: PlatformChatClient = TwitchChatClient(
                auth=platform_auth_container.platform_auth,
                handle_chat_message_use_case=handle_chat_message_use_case,
                handle_reply_use_case=handle_reply_use_case,
                command_router=command_router,
                channel_name=channel_name,
                command_prefix=self._settings.prefix,
                bot_id=bot_user_id,
                bot_name=bot_name,
                logger=self._logger,
            )

            HandleRestoreStreamContextUseCase(
                restore_stream_uow=uow_factories.build_restore_stream_context_uow_factory(),
                minigame_repository=minigame_container.minigame_repository(),
                logger=logger,
            ).handle(channel_name)

            self._chat_client = chat_client

            try:
                await viewer_container.viewer_cache(platform_repository).warmup(channel_name)
            except Exception:
                self._logger.log_error("Не удалось прогреть cache")

            start_word_game_use_case = StartWordGameUseCase(
                minigame_repository=minigame_container.minigame_repository(),
                prefix=self._settings.prefix,
                minigame_uow=uow_factories.build_minigame_uow_factory(),
                db_ro_session=db_ro_session,
                system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
                llm_repository=ai_container.llm_repository,
                command_guess_word=self._settings.command_guess_word,
                command_guess_letter=self._settings.command_guess_letter,
                send_channel_message=chat_client.send_channel_message,
                bot_name=bot_name.lower(),
                logger=logger,
            )

            telegram_bot = provide_telegram_bot(tg_bot_token)
            notifications_repository = provide_notification_repository(telegram_bot)

            post_joke_job: PostJokeJob = joke_container.post_joke_job(
                channel_name=channel_name,
                send_channel_message=chat_client.send_channel_message,
                bot_name=bot_name,
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                conversation_service_provider=ai_container.conversation_service_provider,
                chat_use_case=chat_container.chat_use_case(),
                user_cache=viewer_container.viewer_cache(platform_repository),
                platform_repository=platform_repository,
                generate_response_use_case=generate_response_use_case,
            )

            token_checker_job: TokenCheckerJob = platform_auth_container.token_checker_job

            stream_status_job: StreamStatusJob = get_stream_status_job(
                channel_name=channel_name,
                user_cache=viewer_container.viewer_cache(platform_repository),
                platform_repository=platform_repository,
                stream_status_uow_factory=uow_factories.build_stream_status_uow_factory(),
                minigame_repository=minigame_container.minigame_repository(),
                notification_repository=notifications_repository,
                notification_group_id=self._settings.group_id,
                generate_response_use_case=generate_response_use_case,
                state=chat_summary_state,
                logger=logger,
            )

            chat_summarizer_job: ChatSummarizerJob = chat_container.chat_summarizer_job(
                channel_name=channel_name,
                stream_repository_provider=stream_container.stream_repository_provider,
                generate_response_use_case=generate_response_use_case,
                chat_summary_state=chat_summary_state,
            )

            minigame_job: MinigameTickJob = MinigameTickJob(
                channel_name=channel_name,
                handle_minigame_tick_use_case=HandleMinigameTickUseCase(
                    minigame_repository=minigame_container.minigame_repository(),
                    minigame_ouw=uow_factories.build_minigame_uow_factory(),
                    start_number_guess_game_use_case=StartNumberGuessGameUseCase(
                        minigame_repository=minigame_container.minigame_repository(),
                        prefix=self._settings.prefix,
                        command_name=self._settings.command_guess,
                        send_channel_message=chat_client.send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=bot_name.lower(),
                    ),
                    start_word_game_use_case=start_word_game_use_case,
                    start_rps_game_use_case=StartRpsGameUseCase(
                        minigame_repository=minigame_container.minigame_repository(),
                        prefix=self._settings.prefix,
                        command_name=self._settings.command_rps,
                        send_channel_message=chat_client.send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=bot_name.lower(),
                    ),
                    finish_rps_game_use_case=FinishRpsUseCase(
                        minigame_repository=minigame_container.minigame_repository(),
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=bot_name.lower(),
                        send_channel_message=chat_client.send_channel_message,
                    ),
                    finish_expired_games_use_case=FinishExpiredGamesUseCase(
                        minigame_repository=minigame_container.minigame_repository(),
                        send_channel_message=chat_client.send_channel_message,
                        minigame_uow=uow_factories.build_minigame_uow_factory(),
                        bot_name=bot_name.lower(),
                    ),
                ),
                logger=logger,
            )

            viewer_time_job: ViewerTimeJob = ViewerTimeJob(
                channel_name=channel_name,
                handle_viewer_time_use_case=RewardViewerTimeUseCase(
                    reward_viewer_time_uow=uow_factories.build_viewer_time_uow_factory(),
                    user_cache=viewer_container.viewer_cache(platform_repository),
                    platform_repository=platform_repository,
                ),
                bot_nick=bot_name,
                logger=logger,
            )

            followers_sync_job: FollowersSyncJob = FollowersSyncJob(
                channel_name=channel_name,
                handle_followers_sync_use_case=HandleFollowersSyncUseCase(
                    platform_repository=platform_repository,
                    sync_followers_uow=uow_factories.build_followers_sync_uow_factory(),
                ),
                logger=logger,
            )

            jobs = [
                post_joke_job,
                token_checker_job,
                stream_status_job,
                chat_summarizer_job,
                minigame_job,
                viewer_time_job,
                followers_sync_job,
            ]

            tasks = [Task(job.name, job.run) for job in jobs]
            self._task_runner: TaskRunner = BackgroundTaskRunner(tasks)
            self._task_runner.start_all()

            self._status = BotStatus.RUNNING
            self._started_at = datetime.now(UTC)
            self._last_error = None
            self._task = asyncio.create_task(self._chat_client.start_chat())
            self._task.add_done_callback(self._on_bot_done)

            return BotActionResultResponse(**self.get_status().model_dump(), message="Запуск инициализирован")

    async def stop_bot(self) -> BotActionResultResponse:
        async with self._lock:
            task = self._task

            if not isinstance(task, asyncio.Task):
                self._logger.log_info("Попытка остановки, но бот не запущен")
                return BotActionResultResponse(**self.get_status().model_dump(), message="Бот уже остановлен")
            try:
                self._status: BotStatus = BotStatus.STOPPED
                await self._api_client.close()
                await self._task_runner.cancel_all()
                await self._chat_client.stop_chat()
            except asyncio.CancelledError:
                self._logger.log_debug("Задача бота отменена")
            except Exception as e:
                self._logger.log_exception("Error stopping bot", e)

            return BotActionResultResponse(**self.get_status().model_dump(), message="Бот остановлен")
