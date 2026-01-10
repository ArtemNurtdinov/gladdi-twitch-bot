from __future__ import annotations

import asyncio
import logging

from twitchio.ext import commands

from app.platform.bot.bot_settings import BotSettings
from app.twitch.infrastructure.adapters.chat_context_adapter import as_chat_context
from app.twitch.infrastructure.auth import TwitchAuth
from core.chat.interfaces import ChatClient, ChatContext, ChatMessage, CommandHandler, CommandRouter
from core.chat.outbound import ChatOutbound

logger = logging.getLogger(__name__)


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


class TwitchChatClient(commands.Bot, ChatClient, ChatOutbound):
    def __init__(self, twitch_auth: TwitchAuth, settings: BotSettings):
        self._command_router: CommandRouter | None = None
        self._chat_event_handler = None
        self.bot_nick = lambda: ""
        self._prefix = settings.prefix
        self._initial_channels = [settings.channel_name] if settings.channel_name else []
        super().__init__(token=twitch_auth.access_token, prefix=self._prefix, initial_channels=self._initial_channels)

    def set_router(self, router: CommandRouter) -> None:
        self._command_router = router

    def set_chat_event_handler(self, handler, bot_nick: str):
        self._chat_event_handler = handler
        self.bot_nick = bot_nick

    async def start(self) -> None:
        await super().start()

    async def stop(self) -> None:
        await super().close()

    async def event_ready(self):
        logger.info("TwitchChatClient ready. Channels: %s", ", ".join(self._initial_channels))

    async def event_message(self, message):
        if not self._command_router:
            logger.error("CommandRouter is not set for TwitchChatClient")
            return

        if message.author is None:
            return

        chat_message = ChatMessage()
        chat_message.channel = message.channel.name
        chat_message.author = message.author.display_name
        chat_message.text = message.content

        chat_ctx = as_chat_context(message)
        if isinstance(self._command_router, TwitchCommandRouter):
            self._command_router.set_runtime_context(chat_ctx)

        handled = False
        try:
            handled = await self._command_router.dispatch(chat_message)
        except Exception:
            logger.exception("Ошибка обработки сообщения: %s", message.content)
        if handled:
            return
        if message.content.startswith(self._prefix):
            logger.debug("Неизвестная команда: %s", message.content)
            return

        if self._chat_event_handler:
            try:
                await self._chat_event_handler.handle(
                    channel_name=message.channel.name,
                    display_name=chat_message.author,
                    message=message.content,
                    bot_nick=self.bot_nick,
                )
            except Exception:
                logger.exception("Ошибка в ChatEventHandler для сообщения: %s", message.content)

    @staticmethod
    def _split_text(text: str, max_length: int = 500) -> list[str]:
        if len(text) <= max_length:
            return [text]

        messages: list[str] = []
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

    async def send_channel_message(self, channel_name: str, message: str):
        channel = self.get_channel(channel_name)
        if not channel:
            logger.warning("Канал %s недоступен для отправки сообщения", channel_name)
            return
        for msg in self._split_text(message):
            await channel.send(msg)
            await asyncio.sleep(0.3)

    async def post_message(self, message: str, chat_ctx: ChatContext):
        for msg in self._split_text(message):
            await chat_ctx.send_channel(msg)
            await asyncio.sleep(0.3)
