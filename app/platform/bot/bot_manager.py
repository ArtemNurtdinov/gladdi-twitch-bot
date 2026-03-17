import asyncio
import logging
from collections.abc import Callable
from datetime import datetime

from app.ai.gen.application.use_cases.chat_response_use_case import ChatResponseUseCase
from app.chat.application.model.chat_summary_state import ChatSummaryState
from app.commands.application.commands_registry import CommandRegistryProtocol
from app.commands.follow.application.followage_port import FollowagePort
from app.platform.auth.platform_auth import PlatformAuth
from app.platform.bot.model.bot_settings import BotSettings
from app.platform.bot.schemas import BotActionResult, BotStatus, BotStatusEnum
from app.platform.providers import PlatformApiClient
from app.stream.application.port.stream_info_port import StreamInfoPort
from app.twitch.infrastructure.adapters.chatters_adapter import ChattersApiAdapter
from app.twitch.infrastructure.adapters.followage_adapter import FollowageApiAdapter
from app.twitch.infrastructure.adapters.moderation_adapter import ModerationApiAdapter
from app.twitch.infrastructure.adapters.stream_adapter import StreamApiAdapter
from app.twitch.infrastructure.adapters.twitch_platform_adapter import TwitchStreamingPlatformAdapter
from app.twitch.infrastructure.adapters.user_info_adapter import UserInfoApiAdapter
from app.twitch.infrastructure.helix.client import TwitchHelixClient
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.user.application.ports.user_info_port import UserInfoPort
from app.viewer.application.ports.stream_chatters_port import StreamChattersPort
from bootstrap.chat_composition import build_chat_event_handler
from bootstrap.commands_composition import build_command_registry
from bootstrap.jobs_composition import build_background_tasks
from bootstrap.providers_bundle import build_providers_bundle
from bootstrap.stream_composition import restore_stream_context
from bootstrap.uow_composition import create_uow_factories
from core.background.tasks import BackgroundTasks
from core.chat.interfaces import CommandRouter
from core.chat.outbound import ChatOutbound
from core.db import db_ro_session, db_rw_session

logger = logging.getLogger(__name__)


class BotManager:
    def __init__(
        self,
        settings: BotSettings,
        platform_auth_factory: Callable[[str, str, str, str], PlatformAuth],
        chat_client_factory: Callable[[PlatformAuth, BotSettings, str], ChatOutbound],
        command_router_builder: Callable[[BotSettings, CommandRegistryProtocol, dict[str, str | None]], CommandRouter],
    ):
        self._settings = settings
        self._platform_auth_factory = platform_auth_factory
        self._chat_client_factory = chat_client_factory
        self._command_router_builder = command_router_builder

        self._background_tasks: BackgroundTasks | None = None

        self._chat_client: ChatOutbound | None = None
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

            platform_auth = self._platform_auth_factory(access_token, refresh_token, client_id, client_secret)

            streaming_client = TwitchHelixClient(platform_auth)
            user_info_port: UserInfoPort = UserInfoApiAdapter(streaming_client)
            followage_port: FollowagePort = FollowageApiAdapter(streaming_client, user_info_port)
            stream_info_port: StreamInfoPort = StreamApiAdapter(streaming_client, user_info_port)
            stream_chatters_port: StreamChattersPort = ChattersApiAdapter(streaming_client)
            moderation_port = ModerationApiAdapter(streaming_client)

            streaming_client = TwitchApiService(
                streaming_client=streaming_client,
                user_info_port=user_info_port,
                followage_port=followage_port,
                stream_info_port=stream_info_port,
                stream_chatters_port=stream_chatters_port,
                moderation_port=moderation_port,
            )

            streaming_platform = TwitchStreamingPlatformAdapter(streaming_client)

            self._streaming_client = streaming_client

            providers_bundle = build_providers_bundle(
                streaming_platform=streaming_platform,
                tg_bot_token=tg_bot_token,
                llmbox_host=llmbox_host,
                intent_detector_host=intent_detector_host,
            )

            uow_factories = create_uow_factories(
                session_factory_rw=db_rw_session,
                session_factory_ro=db_ro_session,
                providers=providers_bundle,
            )

            bot_user = await streaming_platform.get_user_by_login(self._settings.bot_name)
            bot_user_id = bot_user.id if bot_user else None
            chat_client = self._chat_client_factory(platform_auth, self._settings, bot_user_id)

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
                streaming_platform=streaming_platform,
            )

            command_registry = build_command_registry(
                providers=providers_bundle,
                uow_factories=uow_factories,
                settings=self._settings,
                bot_name=self._settings.bot_name,
                chat_response_use_case=chat_response_use_case,
                streaming_platform=streaming_platform,
                post_message_fn=chat_client.post_message,
            )

            chat_events_handler = build_chat_event_handler(
                providers=providers_bundle,
                uow_factories=uow_factories,
                chat_response_use_case=chat_response_use_case,
                send_channel_message=chat_client.send_channel_message,
            )
            command_router = self._command_router_builder(self._settings, command_registry, battle_waiting_user)

            chat_client.set_chat_event_handler(chat_events_handler)
            chat_client.set_router(command_router)

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

            self._task = asyncio.create_task(self._chat_client.start())
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
                    await self._chat_client.stop()
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
