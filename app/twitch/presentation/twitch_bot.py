import asyncio
import logging

from twitchio.ext import commands

from app.twitch.bootstrap.bot_settings import BotSettings
from app.twitch.bootstrap.twitch import TwitchProviders
from app.twitch.presentation.background.bot_tasks import BotBackgroundTasks
from app.twitch.presentation.background.model.state import ChatSummaryState
from app.twitch.presentation.interaction.chat_context_adapter import as_chat_context
from app.twitch.presentation.interaction.chat_event_handler import ChatEventHandler
from app.user.bootstrap import UserProviders
from core.chat.interfaces import ChatMessage, CommandRouter

logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self, twitch_providers: TwitchProviders, user_providers: UserProviders, settings: BotSettings):
        self._settings = settings
        self._twitch = twitch_providers
        self._user = user_providers

        self._prefix = self._settings.prefix
        self.initial_channels = [self._settings.channel_name]
        super().__init__(token=twitch_providers.twitch_auth.access_token, prefix=self._prefix, initial_channels=self.initial_channels)

        self._chat_summary_state = ChatSummaryState()
        self._battle_waiting_user_ref = {"value": None}

        self.minigame_orchestrator = None
        self._background_tasks: BotBackgroundTasks | None = None
        self._command_registry = None
        self._chat_event_handler: ChatEventHandler | None = None
        self._command_router: CommandRouter | None = None

        logger.info("Twitch бот инициализирован успешно")

    @property
    def battle_waiting_user_ref(self):
        return self._battle_waiting_user_ref

    @property
    def chat_summary_state(self):
        return self._chat_summary_state

    def set_minigame_orchestrator(self, orchestrator):
        self.minigame_orchestrator = orchestrator

    def set_background_tasks(self, background_tasks: BotBackgroundTasks):
        self._background_tasks = background_tasks

    def set_command_registry(self, command_registry):
        self._command_registry = command_registry

    def set_chat_event_handler(self, chat_event_handler: ChatEventHandler):
        self._chat_event_handler = chat_event_handler

    def set_command_router(self, command_router: CommandRouter):
        self._command_router = command_router

    @property
    def command_router(self) -> CommandRouter | None:
        return self._command_router

    async def _warmup_broadcaster_id(self):
        try:
            if not self.initial_channels:
                logger.warning("Список каналов пуст, пропускаем прогрев кеша ID")
                return

            channel_name = self.initial_channels[0]
            await self._user.user_cache.warmup(channel_name)
        except Exception as e:
            logger.error(f"Не удалось прогреть кеш ID канала: {e}")

    async def _start_background_tasks(self):
        if not self._background_tasks:
            logger.warning("Фоновые задачи не сконфигурированы, пропускаем запуск")
            return
        self._background_tasks.start_all()

    async def close(self):
        if self._background_tasks:
            await self._background_tasks.stop_all()
        await super().close()

    async def event_ready(self):
        logger.info(f"Бот {self.nick} готов")
        if self.initial_channels:
            logger.info(f"Бот успешно подключен к каналу: {', '.join(self.initial_channels)}")
        else:
            logger.error("Проблемы с подключением к каналам!")
        await self._warmup_broadcaster_id()
        await self._start_background_tasks()

    async def event_channel_joined(self, channel):
        logger.info(f"Успешно подключились к каналу: {channel.name}")

    async def event_channel_join_failure(self, channel):
        logger.error(f"Не удалось подключиться к каналу {channel}")

    async def event_message(self, message):
        if not message.author:
            return

        if message.content.startswith(self._prefix):
            if self._command_router:
                chat_ctx = as_chat_context(message)
                chat_message = ChatMessage()
                chat_message.channel = message.channel.name
                chat_message.author = message.author.display_name
                chat_message.author_id = getattr(message.author, "id", None)
                chat_message.text = message.content
                if hasattr(self._command_router, "set_runtime_context"):
                    # TwitchCommandRouter uses runtime ctx for handlers
                    try:
                        self._command_router.set_runtime_context(chat_ctx)  # type: ignore[attr-defined]
                    except Exception:
                        logger.debug("Command router does not support runtime context")
                await self._command_router.dispatch(chat_message)
            return

        if not self._chat_event_handler:
            logger.error("ChatEventHandler не сконфигурирован")
            return

        await self._chat_event_handler.handle(
            channel_name=message.channel.name, display_name=message.author.display_name, message=message.content, bot_nick=self.nick
        )

    def _split_text(self, text, max_length=500):
        if len(text) <= max_length:
            return [text]

        messages = []
        while text:
            if len(text) <= max_length:
                messages.append(text)
                break

            split_pos = text.rfind(" ", 0, max_length)

            if split_pos == -1:
                split_pos = max_length

            part = text[:split_pos].strip()
            if part:
                messages.append(part)

            text = text[split_pos:].strip()
        return messages

    async def post_message_in_twitch_chat(self, message: str, ctx):
        chat_ctx = as_chat_context(ctx)
        messages = self._split_text(message)

        for msg in messages:
            await chat_ctx.send_channel(msg)
            await asyncio.sleep(0.3)

    async def send_channel_message(self, channel_name: str, message: str):
        channel = self.get_channel(channel_name)
        if not channel:
            logger.warning(f"Канал {channel_name} недоступен для отправки сообщения")
            return

        messages = self._split_text(message)
        for msg in messages:
            await channel.send(msg)
            await asyncio.sleep(0.3)
