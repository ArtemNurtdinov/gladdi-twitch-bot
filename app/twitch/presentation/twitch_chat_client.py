from __future__ import annotations

import logging

from twitchio import Message
from twitchio.ext import commands

from app.twitch.bootstrap.bot_settings import BotSettings
from app.twitch.infrastructure.auth import TwitchAuth
from core.chat.interfaces import ChatClient, ChatContext, ChatMessage, CommandHandler, CommandRouter

logger = logging.getLogger(__name__)


class TwitchChatContext(ChatContext):
    def __init__(self, message: Message):
        self._message = message

    @property
    def channel(self) -> str:
        return self._message.channel.name

    @property
    def author(self) -> str:
        return self._message.author.display_name

    async def reply(self, text: str) -> None:
        await self._message.channel.send(text)

    async def send_channel(self, text: str) -> None:
        await self._message.channel.send(text)


class TwitchCommandRouter(CommandRouter):
    def __init__(self, prefix: str):
        self._prefix = prefix
        self._handlers: dict[str, CommandHandler] = {}
        self._runtime_ctx: ChatContext | None = None

    def set_runtime_context(self, ctx: ChatContext) -> None:
        self._runtime_ctx = ctx

    def register(self, name: str, handler: CommandHandler) -> None:
        self._handlers[name.lower()] = handler

    async def dispatch(self, message: ChatMessage) -> bool:
        if not message.text.startswith(self._prefix):
            return False

        without_prefix = message.text[len(self._prefix) :].strip()
        if not without_prefix:
            return False
        parts = without_prefix.split(" ", 1)
        cmd_name = parts[0].lower()
        handler = self._handlers.get(cmd_name)
        if not handler:
            return False

        if not self._runtime_ctx:
            logger.warning("Runtime ChatContext is not set for TwitchCommandRouter")
            return False

        try:
            await handler(self._runtime_ctx, message)
        finally:
            self._runtime_ctx = None
        return True


class TwitchChatClient(commands.Bot, ChatClient):
    def __init__(self, twitch_auth: TwitchAuth, settings: BotSettings):
        self._router: CommandRouter | None = None
        self._prefix = settings.prefix
        self._initial_channels = [settings.channel_name] if settings.channel_name else []
        super().__init__(token=twitch_auth.access_token, prefix=self._prefix, initial_channels=self._initial_channels)

    def set_router(self, router: CommandRouter) -> None:
        self._router = router

    async def start(self) -> None:
        await super().start()

    async def stop(self) -> None:
        await super().close()

    async def event_ready(self):
        logger.info("TwitchChatClient ready. Channels: %s", ", ".join(self._initial_channels))

    async def event_message(self, message):
        if not self._router:
            logger.error("CommandRouter is not set for TwitchChatClient")
            return

        chat_message = ChatMessage()
        chat_message.channel = message.channel.name
        chat_message.author = message.author.display_name
        chat_message.text = message.content

        chat_ctx = TwitchChatContext(message)
        if isinstance(self._router, TwitchCommandRouter):
            self._router.set_runtime_context(chat_ctx)

        handled = False
        try:
            handled = await self._router.dispatch(chat_message)
        except Exception:
            logger.exception("Ошибка обработки сообщения: %s", message.content)
        if not handled and message.content.startswith(self._prefix):
            logger.debug("Неизвестная команда: %s", message.content)
