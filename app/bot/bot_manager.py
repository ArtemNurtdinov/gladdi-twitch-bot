import asyncio
from datetime import UTC, datetime

from app.ai.gen.di.container import AIContainer
from app.battle.di.container import BattleContainer
from app.betting.di.container import BettingContainer
from app.bot.domain.model.status import BotStatus
from app.bot.presentation.api.model.response.action import BotActionResultResponse
from app.bot.presentation.api.model.response.status import BotStatusResponse
from app.chat.application.job.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.chat.di.container import ChatContainer
from app.chat.infrastructure.chat_repository import ChatRepositoryImpl
from app.core.config.domain.model.bot import BotConfig
from app.core.config.domain.model.intent_detector import IntentDetectorConfig
from app.core.config.domain.model.llmbox import LLMBoxConfig
from app.core.config.domain.model.telegram import TelegramConfig
from app.core.logger.domain.logger import Logger
from app.core.network.api.client import ApiClient
from app.economy.di.container import EconomyContainer
from app.equipment.di.container import EquipmentContainer
from app.follow.di.container import FollowContainer
from app.joke.application.job.post_joke_job import PostJokeJob
from app.joke.di.container import JokeContainer
from app.minigame.application.job.minigame_tick_job import MinigameTickJob
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
from app.platform.command.battle.application.battle_command_handler import BattleCommandHandlerImpl
from app.platform.command.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.domain.command_router import CommandRouter
from app.platform.di.container import PlatformContainer
from app.shop.di.container import ShopContainer
from app.stream.application.usecase.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.di.container import StreamContainer
from app.task.domain.model.task import Task
from app.task.domain.runner import TaskRunner
from app.task.infrastructure.runner import BackgroundTaskRunner
from app.viewer.di.container import ViewerContainer
from core.db import db_ro_session, db_rw_session
from core.provider import Provider


class BotManager:
    def __init__(
        self,
        config: BotConfig,
        telegram_config: TelegramConfig,
        llmbox_config: LLMBoxConfig,
        intent_detector_config: IntentDetectorConfig,
        logger: Logger,
    ):
        self._config = config
        self._telegram_config = telegram_config
        self._llmbox_config = llmbox_config
        self._intent_detector_config = intent_detector_config
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
        client_id: str,
        client_secret: str,
        channel_name: str,
    ) -> BotActionResultResponse:
        async with self._lock:
            if self._task and not self._task.done():
                return BotActionResultResponse(**self.get_status().model_dump(), message="Бот уже запущен")

            platform_auth_container = PlatformAuthContainer(access_token, refresh_token, client_id, client_secret, self._logger)
            viewer_container = ViewerContainer()
            ai_container = AIContainer(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                llmbox_host=self._llmbox_config.host,
                intent_detector_host=self._intent_detector_config.host,
            )
            ask_container = AskContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
            joke_container = JokeContainer(self._logger)
            stream_container = StreamContainer()
            follow_container = FollowContainer()
            economy_container = EconomyContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
            equipment_container = EquipmentContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
            shop_container = ShopContainer()
            minigame_container = MinigameContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session, logger=self._logger)
            battle_container = BattleContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session)
            betting_container = BettingContainer()
            chat_container = ChatContainer(session_factory_rw=db_rw_session, session_factory_ro=db_ro_session, logger=self._logger)
            platform_container = PlatformContainer(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                platform_auth_container=platform_auth_container,
                logger=self._logger,
            )

            minigame_repository = minigame_container.minigame_repository()
            self._api_client = platform_container.api_client

            bot_user = await platform_container.platform_repository().get_authenticated_user()
            if not bot_user:
                raise ValueError("Не удалось получить профиль бота по токену (GET /users). Проверьте авторизацию.")
            bot_name = bot_user.display_name.lower()
            bot_user_id = bot_user.id
            battle_waiting_user = {"value": None}
            chat_summary_state = ChatSummaryState()

            moderation_service = ModerationService(
                platform_repository=platform_container.platform_repository(),
                user_cache=viewer_container.viewer_cache(platform_container.platform_repository()),
                logger=self._logger,
            )

            followage_command_handler = platform_container.followage_command_handler(
                command_prefix=self._config.prefix,
                command_name=self._config.command_followage,
                generate_response_use_case=ai_container.generate_response_use_case(),
                chat_repo_provider=chat_container.chat_repository_provider,
                conversation_service_provider=ai_container.conversation_service_provider,
                system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
                platform_repository=platform_container.platform_repository(),
                bot_name=bot_name,
            )

            ask_ouw_factory = ask_container.ask_uow_factory(
                chat_repository_provider=Provider(lambda session: ChatRepositoryImpl(session)),
                conversation_service_provider=ai_container.conversation_service_provider,
                system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
            )

            ask_command_handler: CommandHandler = AskCommandHandlerImpl(
                command_prefix=self._config.prefix,
                command_name=self._config.command_gladdi,
                handle_ask_use_case=HandleAskUseCase(
                    get_intent_from_text_use_case=ai_container.get_intent_from_text_use_case(),
                    prompt_service=ai_container.prompt_service,
                    unit_of_work_factory=ask_ouw_factory,
                    chat_response_use_case=ai_container.generate_response_use_case(),
                ),
                bot_nick=bot_name,
            )

            battle_command_handler: CommandHandler = BattleCommandHandlerImpl(
                command_prefix=self._config.prefix,
                command_name=self._config.command_fight,
                handle_battle_use_case=HandleBattleUseCase(
                    battle_uow=battle_container.battle_uow_factory(
                        economy_policy_provider=economy_container.economy_policy_provider,
                        chat_use_case=chat_container.chat_use_case(),
                        conversation_service_provider=ai_container.conversation_service_provider,
                        get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                    ),
                    chat_response_use_case=ai_container.generate_response_use_case(),
                    calculate_timeout_use_case=equipment_container.calculate_timeout_use_case(),
                ),
                chat_moderation=moderation_service,
                bot_name=bot_name,
                battle_waiting_user=battle_waiting_user,
            )

            roll_command_handler = platform_container.roll_command_handler(
                command_prefix=self._config.prefix,
                command_name=self._config.command_roll,
                economy_policy_provider=economy_container.economy_policy_provider,
                betting_service_provider=betting_container.betting_service_provider,
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                chat_use_case=chat_container.chat_use_case(),
                roll_cooldown_use_case=equipment_container.roll_cooldown_use_case(),
                calculate_timeout_use_case=equipment_container.calculate_timeout_use_case(),
                chat_moderation_port=moderation_service,
                bot_name=bot_name,
            )

            balance_command_handler: CommandHandler = BalanceCommandHandlerImpl(
                handle_balance_use_case=economy_container.handle_balance_use_case(chat_use_case=chat_container.chat_use_case()),
                bot_name=bot_name,
            )

            bonus_command_handler = platform_container.bonus_command_handler(
                stream_repository_provider=stream_container.stream_repository_provider,
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                bot_name=bot_name,
            )

            transfer_command_handler = platform_container.transfer_command_handler(
                command_prefix=self._config.prefix,
                command_name=self._config.command_transfer,
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                bot_name=bot_name,
            )

            shop_command_handler = platform_container.shop_command_handler(
                command_prefix=self._config.prefix,
                command_shop_name=self._config.command_shop,
                command_buy_name=self._config.command_buy,
                economy_policy_provider=economy_container.economy_policy_provider,
                add_equipment_use_case=equipment_container.add_equipment_use_case(),
                equipment_exists_use_case=equipment_container.equipment_exists_use_case(),
                chat_use_case=chat_container.chat_use_case(),
                shop_item_repository_provider=shop_container.shop_item_repository_provider,
                bot_name=bot_name,
            )

            buy_command_handler = platform_container.buy_command_handler(
                command_prefix=self._config.prefix,
                command_buy_name=self._config.command_buy,
                economy_policy_provider=economy_container.economy_policy_provider,
                add_equipment_use_case=equipment_container.add_equipment_use_case(),
                equipment_exists_use_case=equipment_container.equipment_exists_use_case(),
                chat_use_case=chat_container.chat_use_case(),
                shop_item_repository_provider=shop_container.shop_item_repository_provider,
                bot_name=bot_name,
            )

            equipment_command_handler = platform_container.equipment_command_handler(
                command_prefix=self._config.prefix,
                command_shop=self._config.command_shop,
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                chat_use_case=chat_container.chat_use_case(),
                bot_name=bot_name,
            )

            top_command_handler = platform_container.top_command_handler(
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                bot_name=bot_name,
            )

            bottom_command_handler = platform_container.bottom_command_handler(
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                bot_name=bot_name,
            )

            commands = {
                self._config.command_balance,
                self._config.command_bonus,
                f"{self._config.command_roll} [сумма]",
                f"{self._config.command_transfer} @ник сумма",
                self._config.command_shop,
                f"{self._config.command_buy} название",
                self._config.command_equipment,
                self._config.command_top,
                self._config.command_bottom,
                self._config.command_stats,
                self._config.command_fight,
                f"{self._config.command_gladdi} текст",
                self._config.command_followage,
            }

            help_command_handler = platform_container.help_command_handler(
                command_prefix=self._config.prefix, chat_use_case=chat_container.chat_use_case(), commands=commands, bot_name=bot_name
            )

            stats_command_handler = platform_container.stats_command_handler(
                command_prefix=self._config.prefix,
                command_name=self._config.command_stats,
                economy_policy_provider=economy_container.economy_policy_provider,
                betting_service_provider=betting_container.betting_service_provider,
                battle_use_case=battle_container.battle_use_case(),
                chat_use_case=chat_container.chat_use_case(),
                bot_name=bot_name,
            )

            guess_number_command_handler = platform_container.guess_number_command_handler(
                command_prefix=self._config.prefix,
                command_name=self._config.command_guess,
                minigame_repository=minigame_repository,
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                bot_name=bot_name,
            )

            guess_letter_command_handler = platform_container.guess_letter_command_handler(
                command_prefix=self._config.prefix,
                command_name=self._config.command_guess_letter,
                minigame_repository=minigame_repository,
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                bot_name=bot_name,
            )

            guess_word_command_handler = platform_container.guess_word_command_handler(
                command_prefix=self._config.prefix,
                command_name=self._config.command_guess_word,
                minigame_repository=minigame_repository,
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                bot_name=bot_name,
            )

            rps_command_handler = platform_container.rps_command_handler(
                command_prefix=self._config.prefix,
                command_name=self._config.command_rps,
                minigame_repository=minigame_repository,
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                bot_name=bot_name,
            )

            command_router: CommandRouter = CommandRouterImpl(self._config.prefix)

            command_router.register_command_handler(self._config.command_followage, followage_command_handler)
            command_router.register_command_handler(self._config.command_gladdi, ask_command_handler)
            command_router.register_command_handler(self._config.command_fight, battle_command_handler)
            command_router.register_command_handler(self._config.command_roll, roll_command_handler)
            command_router.register_command_handler(self._config.command_balance, balance_command_handler)
            command_router.register_command_handler(self._config.command_bonus, bonus_command_handler)
            command_router.register_command_handler(self._config.command_transfer, transfer_command_handler)
            command_router.register_command_handler(self._config.command_shop, shop_command_handler)
            command_router.register_command_handler(self._config.command_buy, buy_command_handler)
            command_router.register_command_handler(self._config.command_equipment, equipment_command_handler)
            command_router.register_command_handler(self._config.command_top, top_command_handler)
            command_router.register_command_handler(self._config.command_bottom, bottom_command_handler)
            command_router.register_command_handler(self._config.command_help, help_command_handler)
            command_router.register_command_handler(self._config.command_stats, stats_command_handler)
            command_router.register_command_handler(self._config.command_guess, guess_number_command_handler)
            command_router.register_command_handler(self._config.command_guess_letter, guess_letter_command_handler)
            command_router.register_command_handler(self._config.command_guess_word, guess_word_command_handler)
            command_router.register_command_handler(self._config.command_rps, rps_command_handler)

            handle_chat_message_use_case = HandleChatMessageUseCase(
                unit_of_work_factory=chat_container.chat_message_uow_factory(
                    economy_policy_provider=economy_container.economy_policy_provider,
                    stream_repository_provider=stream_container.stream_repository_provider,
                    viewer_repository_provider=viewer_container.viewer_repository_provider,
                    conversation_service_provider=ai_container.conversation_service_provider,
                    system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
                ),
                get_intent_from_text_use_case=ai_container.get_intent_from_text_use_case(),
                prompt_service=ai_container.prompt_service,
                generate_response_use_case=ai_container.generate_response_use_case(),
            )

            handle_reply_use_case = HandleReplyUseCase(
                chat_message_uow=chat_container.chat_message_uow_factory(
                    economy_policy_provider=economy_container.economy_policy_provider,
                    stream_repository_provider=stream_container.stream_repository_provider,
                    viewer_repository_provider=viewer_container.viewer_repository_provider,
                    conversation_service_provider=ai_container.conversation_service_provider,
                    system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
                ),
                prompt_service=ai_container.prompt_service,
                generate_response_use_case=ai_container.generate_response_use_case(),
            )

            chat_client: PlatformChatClient = TwitchChatClient(
                auth=platform_auth_container.platform_auth,
                handle_chat_message_use_case=handle_chat_message_use_case,
                handle_reply_use_case=handle_reply_use_case,
                command_router=command_router,
                channel_name=channel_name,
                command_prefix=self._config.prefix,
                bot_id=bot_user_id,
                bot_name=bot_name,
                logger=self._logger,
            )

            HandleRestoreStreamContextUseCase(
                restore_stream_uow=platform_container.restore_stream_uow(stream_container.stream_repository_provider),
                minigame_repository=minigame_repository,
                logger=self._logger,
            ).handle(channel_name)

            self._chat_client = chat_client

            try:
                await viewer_container.viewer_cache(platform_container.platform_repository()).warmup(channel_name)
            except Exception:
                self._logger.log_error("Не удалось прогреть cache")

            telegram_bot = provide_telegram_bot(self._telegram_config.bot_token)
            notifications_repository = provide_notification_repository(telegram_bot)

            post_joke_job: PostJokeJob = joke_container.post_joke_job(
                channel_name=channel_name,
                send_channel_message=chat_client.send_channel_message,
                bot_name=bot_name,
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                conversation_service_provider=ai_container.conversation_service_provider,
                chat_use_case=chat_container.chat_use_case(),
                user_cache=viewer_container.viewer_cache(platform_container.platform_repository()),
                platform_repository=platform_container.platform_repository(),
                generate_response_use_case=ai_container.generate_response_use_case(),
            )

            token_checker_job: TokenCheckerJob = platform_auth_container.token_checker_job

            stream_status_job = platform_container.stream_status_job(
                channel_name=channel_name,
                user_cache=viewer_container.viewer_cache(platform_container.platform_repository()),
                platform_repository=platform_container.platform_repository(),
                minigame_repository=minigame_repository,
                notification_repository=notifications_repository,
                notification_group_id=self._telegram_config.group_id,
                generate_response_use_case=ai_container.generate_response_use_case(),
                state=chat_summary_state,
                stream_repository_provider=stream_container.stream_repository_provider,
                viewer_repository_provider=viewer_container.viewer_repository_provider,
                battle_use_case=battle_container.battle_use_case(),
                economy_policy_provider=economy_container.economy_policy_provider,
                chat_use_case=chat_container.chat_use_case(),
                conversation_service_provider=ai_container.conversation_service_provider,
            )

            chat_summarizer_job: ChatSummarizerJob = chat_container.chat_summarizer_job(
                channel_name=channel_name,
                stream_repository_provider=stream_container.stream_repository_provider,
                generate_response_use_case=ai_container.generate_response_use_case(),
                chat_summary_state=chat_summary_state,
            )

            minigame_job: MinigameTickJob = MinigameTickJob(
                channel_name=channel_name,
                handle_minigame_tick_use_case=platform_container.handle_minigame_tick_use_case(
                    minigame_repository=minigame_repository,
                    economy_policy_provider=economy_container.economy_policy_provider,
                    chat_use_case=chat_container.chat_use_case(),
                    stream_repository_provider=stream_container.stream_repository_provider,
                    get_used_words_use_case=minigame_container.get_used_words_use_case(),
                    add_used_words_use_case=minigame_container.add_used_word_use_case(),
                    conversation_service_provider=ai_container.conversation_service_provider,
                    get_user_equipment_use_case=equipment_container.get_user_equipment_use_case(),
                    system_prompt_repository_provider=ai_container.system_prompt_repo_provider,
                    llm_repository=ai_container.llm_repository,
                    prefix=self._config.prefix,
                    number_guess_name=self._config.command_guess,
                    command_guess_word=self._config.command_guess_word,
                    command_guess_letter=self._config.command_guess_letter,
                    rps_command_name=self._config.command_rps,
                    send_channel_message=chat_client.send_channel_message,
                    bot_name=bot_name,
                ),
                logger=self._logger,
            )

            viewer_time_job = platform_container.viewer_time_job(
                stream_repository_provider=stream_container.stream_repository_provider,
                viewer_repository_provider=viewer_container.viewer_repository_provider,
                economy_policy_provider=economy_container.economy_policy_provider,
                viewer_cache=viewer_container.viewer_cache(platform_container.platform_repository()),
                platform_repository=platform_container.platform_repository(),
                channel_name=channel_name,
                bot_name=bot_name,
            )

            followers_sync_job = platform_container.followers_sync_job(
                channel_name=channel_name,
                platform_repository=platform_container.platform_repository(),
                followers_repository_provider=follow_container.followers_repository_provider,
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
