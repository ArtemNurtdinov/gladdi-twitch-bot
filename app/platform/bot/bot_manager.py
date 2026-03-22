import asyncio
import logging
from datetime import datetime

from app.ai.gen.application.use_cases.chat_response_use_case import ChatResponseUseCase
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.commands.ask.application.handle_ask_use_case import HandleAskUseCase
from app.commands.ask.infrastructure.ask_command_handler import AskCommandHandlerImpl
from app.commands.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.commands.battle.infrastructure.battle_command_handler import BattleCommandHandlerImpl
from app.commands.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.commands.follow.application.handle_followage_use_case import HandleFollowAgeUseCase
from app.commands.follow.infrastructure.followage_command_handler import FollowageCommandHandlerImpl
from app.moderation.application.moderation_service import ModerationService
from app.platform.auth.infrastructure.twitch_auth import TwitchAuth
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.bot.model.bot_settings import BotSettings
from app.platform.bot.schemas import BotActionResult, BotStatus, BotStatusEnum
from app.platform.chat.application.platform_chat_client import PlatformChatClient
from app.platform.chat.infrastructure.chat_event_handler import ChatEventsHandlerImpl
from app.platform.chat.infrastructure.twitch_chat_client import TwitchChatClient
from app.platform.command.application.command_handler import (
    BalanceHandler,
    BonusHandler,
    BottomHandler,
    BuyHandler,
    EquipmentHandler,
    GuessLetterHandler,
    GuessNumberHandler,
    GuessWordHandler,
    HelpHandler,
    RollHandler,
    RpsHandler,
    ShopHandler,
    StatsHandler,
    TopHandler,
    TransferHandler,
)
from app.platform.command.application.command_router import CommandRouterImpl
from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.domain.command_router import CommandRouter
from app.platform.infrastructure.client import TwitchHelixClient
from app.platform.infrastructure.repository import PlatformRepositoryImpl
from app.platform.providers import PlatformApiClient
from bootstrap.commands_composition import build_command_registry
from bootstrap.jobs_composition import build_background_tasks
from bootstrap.providers_bundle import build_providers_bundle
from bootstrap.stream_composition import restore_stream_context
from bootstrap.uow_composition import create_uow_factories
from core.background.tasks import BackgroundTasks
from core.db import db_ro_session, db_rw_session

logger = logging.getLogger(__name__)


class BotManager:
    def __init__(self, settings: BotSettings):
        self._settings = settings

        self._background_tasks: BackgroundTasks | None = None

        self._chat_client: PlatformChatClient | None = None
        self._task: asyncio.Task | None = None
        self._status: BotStatusEnum = BotStatusEnum.STOPPED
        self._started_at: datetime | None = None
        self._last_error: str | None = None
        self._lock = asyncio.Lock()

        self._streaming_client: PlatformApiClient | None = None

    def _reset_state(self):
        self._background_tasks = None
        self._chat_client = None
        self._task = None
        self._status = BotStatusEnum.STOPPED
        self._started_at = None

    def _on_bot_done(self, task: asyncio.Task) -> None:
        try:
            exc = task.exception()
            if exc:
                self._last_error = str(exc)
                logger.error(f"Twitch бот завершился с ошибкой: {exc}")
            else:
                logger.info("Twitch бот остановлен")
        except asyncio.CancelledError:
            logger.info("Задача Twitch бота отменена")
        finally:
            self._reset_state()

    def get_status(self) -> BotStatus:
        started_at = self._started_at.isoformat() if self._started_at else None
        return BotStatus(status=self._status, started_at=started_at, last_error=self._last_error)

    def validate_credentials(self, access_token: str, refresh_token: str, client_id: str, client_secret: str) -> None:
        missing = []
        if not client_id:
            missing.append("client_id")
        if not client_secret:
            missing.append("client_secret")
        if not refresh_token:
            missing.append("refresh_token")
        if not access_token:
            missing.append("access_token")

        if missing:
            raise ValueError(f"Недостаточно данных для авторизации платформы: {', '.join(missing)}")

    async def start_bot(
        self,
        access_token: str,
        refresh_token: str,
        tg_bot_token: str,
        llmbox_host: str,
        intent_detector_host: str,
        client_id: str,
        client_secret: str,
    ) -> BotActionResult:
        async with self._lock:
            if self._task and not self._task.done():
                return BotActionResult(**self.get_status().model_dump(), message="Бот уже запущен")

            self.validate_credentials(access_token, refresh_token, client_id, client_secret)

            platform_auth: PlatformAuth = TwitchAuth(
                access_token=access_token,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                logger=logger,
            )

            streaming_client = TwitchHelixClient(platform_auth)
            platform_repository = PlatformRepositoryImpl(streaming_client)

            self._streaming_client = streaming_client

            providers_bundle = build_providers_bundle(
                platform_repository=platform_repository,
                tg_bot_token=tg_bot_token,
                llmbox_host=llmbox_host,
                intent_detector_host=intent_detector_host,
            )

            uow_factories = create_uow_factories(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                providers=providers_bundle,
                platform_repository=platform_repository,
            )

            bot_user = await platform_repository.get_user_by_login(self._settings.bot_name)
            bot_user_id = bot_user.id if bot_user else None

            chat_client: PlatformChatClient = TwitchChatClient(
                auth=platform_auth,
                channel_name=self._settings.channel_name,
                command_prefix=self._settings.prefix,
                bot_id=bot_user_id,
                bot_name=self._settings.bot_name,
            )

            battle_waiting_user = {"value": None}

            chat_summary_state = ChatSummaryState()

            chat_response_use_case = ChatResponseUseCase(
                unit_of_work_factory=uow_factories.build_chat_response_uow_factory(),
                llm_repository=providers_bundle.ai_providers.llm_repository,
                system_prompt_repository_provider=providers_bundle.ai_providers.system_prompt_repo_provider,
                db_ro_session=db_ro_session,
            )

            self._background_tasks = build_background_tasks(
                providers=providers_bundle,
                uow_factories=uow_factories,
                settings=self._settings,
                bot_name=self._settings.bot_name,
                chat_summary_state=chat_summary_state,
                chat_response_use_case=chat_response_use_case,
                outbound=chat_client,
                platform_auth=platform_auth,
                platform_repository=platform_repository,
            )

            moderation_service = ModerationService(
                platform_repository=platform_repository,
                user_cache=providers_bundle.user_providers.user_cache,
            )

            command_registry = build_command_registry(
                providers=providers_bundle,
                uow_factories=uow_factories,
                settings=self._settings,
                bot_name=self._settings.bot_name,
                send_channel_message=chat_client.send_channel_message,
                moderation_service=moderation_service,
            )

            handle_chat_message = HandleChatMessageUseCase(
                unit_of_work_factory=uow_factories.build_chat_message_uow_factory(),
                get_intent_from_text_use_case=providers_bundle.ai_providers.get_intent_use_case,
                prompt_service=providers_bundle.ai_providers.prompt_service,
                chat_response_use_case=chat_response_use_case,
            )

            chat_events_handler = ChatEventsHandlerImpl(
                handle_chat_message_use_case=handle_chat_message,
                send_channel_message=chat_client.send_channel_message,
            )

            followage_command_handler: CommandHandler = FollowageCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_followage,
                handle_follow_age_use_case=HandleFollowAgeUseCase(
                    chat_repo_provider=providers_bundle.chat_providers.chat_repo_provider,
                    conversation_repo_provider=providers_bundle.ai_providers.conversation_repo_provider,
                    chat_response_use_case=chat_response_use_case,
                    unit_of_work_factory=uow_factories.build_follow_age_uow_factory(),
                ),
                bot_nick=self._settings.bot_name,
                post_message_fn=chat_client.send_channel_message,
            )

            ask_uow_factory = uow_factories.build_ask_uow_factory()

            ask_command_handler: CommandHandler = AskCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_gladdi,
                handle_ask_use_case=HandleAskUseCase(
                    get_intent_from_text_use_case=providers_bundle.ai_providers.get_intent_use_case,
                    prompt_service=providers_bundle.ai_providers.prompt_service,
                    unit_of_work_factory=ask_uow_factory,
                    chat_response_use_case=chat_response_use_case,
                ),
                post_message_fn=chat_client.send_channel_message,
                bot_nick=self._settings.bot_name,
            )

            battle_command_handler: CommandHandler = BattleCommandHandlerImpl(
                command_prefix=self._settings.prefix,
                command_name=self._settings.command_fight,
                handle_battle_use_case=HandleBattleUseCase(
                    battle_uow=uow_factories.build_battle_uow_factory(),
                    chat_response_use_case=chat_response_use_case,
                    calculate_timeout_use_case=providers_bundle.equipment_providers.calculate_timeout_use_case,
                ),
                chat_moderation=moderation_service,
                bot_name=self._settings.bot_name,
                post_message_fn=chat_client.send_channel_message,
                battle_waiting_user=battle_waiting_user,
            )

            roll_handler = RollHandler(command_registry, self._settings.prefix, self._settings.command_roll)
            balance_handler = BalanceHandler(command_registry)
            bonus_handler = BonusHandler(command_registry)
            transfer_handler = TransferHandler(command_registry, self._settings.prefix, self._settings.command_transfer)
            shop_handler = ShopHandler(command_registry)
            buy_handler = BuyHandler(command_registry, self._settings.prefix, self._settings.command_buy)
            equipment_handler = EquipmentHandler(command_registry)
            top_handler = TopHandler(command_registry)
            bottom_handler = BottomHandler(command_registry)
            help_handler = HelpHandler(command_registry)
            stats_handler = StatsHandler(command_registry)
            guess_number_handler = GuessNumberHandler(command_registry, self._settings.prefix, self._settings.command_guess)
            guess_letter_handler = GuessLetterHandler(command_registry, self._settings.prefix, self._settings.command_guess_letter)
            guess_word_handler = GuessWordHandler(command_registry, self._settings.prefix, self._settings.command_guess_word)
            rps_handler = RpsHandler(command_registry, self._settings.prefix, self._settings.command_rps)

            command_router: CommandRouter = CommandRouterImpl(self._settings.prefix)

            command_router.register_command_handler(self._settings.command_followage, followage_command_handler)
            command_router.register_command_handler(self._settings.command_gladdi, ask_command_handler)
            command_router.register_command_handler(self._settings.command_fight, battle_command_handler)
            command_router.register_command_handler(self._settings.command_roll, roll_handler)
            command_router.register_command_handler(self._settings.command_balance, balance_handler)
            command_router.register_command_handler(self._settings.command_bonus, bonus_handler)
            command_router.register_command_handler(self._settings.command_transfer, transfer_handler)
            command_router.register_command_handler(self._settings.command_shop, shop_handler)
            command_router.register_command_handler(self._settings.command_buy, buy_handler)
            command_router.register_command_handler(self._settings.command_equipment, equipment_handler)
            command_router.register_command_handler(self._settings.command_top, top_handler)
            command_router.register_command_handler(self._settings.command_bottom, bottom_handler)
            command_router.register_command_handler(self._settings.command_help, help_handler)
            command_router.register_command_handler(self._settings.command_stats, stats_handler)
            command_router.register_command_handler(self._settings.command_guess, guess_number_handler)
            command_router.register_command_handler(self._settings.command_guess_letter, guess_letter_handler)
            command_router.register_command_handler(self._settings.command_guess_word, guess_word_handler)
            command_router.register_command_handler(self._settings.command_rps, rps_handler)

            chat_client.set_chat_event_handler(chat_events_handler)
            chat_client.set_command_router(command_router)

            restore_stream_context(
                providers=providers_bundle,
                uow_factories=uow_factories,
                channel_name=self._settings.channel_name,
            )

            self._chat_client = chat_client

            try:
                await providers_bundle.user_providers.user_cache.warmup(self._settings.channel_name)
            except Exception:
                logger.error("Не удалось прогреть cache")

            self._background_tasks.start_all()

            self._status = BotStatusEnum.RUNNING
            self._started_at = datetime.utcnow()
            self._last_error = None

            self._task = asyncio.create_task(self._chat_client.start_chat())
            self._task.add_done_callback(self._on_bot_done)

            return BotActionResult(**self.get_status().model_dump(), message="Запуск инициализирован")

    async def stop_bot(self) -> BotActionResult:
        async with self._lock:
            task = self._task
            platform_api_service = self._streaming_client if self._streaming_client else None

            if not isinstance(task, asyncio.Task):
                logger.info("Попытка остановки, но бот не запущен")
                return BotActionResult(**self.get_status().model_dump(), message="Бот уже остановлен")
            try:
                if self._chat_client:
                    await self._chat_client.start_chat()
                if platform_api_service:
                    await platform_api_service.aclose()
                if self._background_tasks:
                    await self._background_tasks.stop_all()
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        logger.debug("Задача бота отменена")
            finally:
                self._reset_state()

            return BotActionResult(**self.get_status().model_dump(), message="Бот остановлен")
