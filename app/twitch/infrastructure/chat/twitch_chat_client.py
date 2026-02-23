from __future__ import annotations

import asyncio
import logging

from twitchio import Client, WebsocketWelcome
from twitchio.eventsub import ChatMessageSubscription
from twitchio.exceptions import HTTPException
from twitchio.models.eventsub_ import ChatMessage as EventSubChatMessage

from app.platform.bot.bot_settings import BotSettings
from app.twitch.infrastructure.helix.auth import TwitchAuth
from core.chat.interfaces import ChatClient, ChatContext, ChatMessage, CommandRouter
from core.chat.outbound import ChatEventsHandler, ChatOutbound
from core.chat.prefix_command_router import PrefixCommandRouter

logger = logging.getLogger(__name__)


class _EventChatContext(ChatContext):
    def __init__(self, client: TwitchChatClient, channel_login: str):
        self._client = client
        self._channel_login = channel_login

    @property
    def channel(self) -> str:
        return self._channel_login

    async def send_channel(self, text: str) -> None:
        await self._client.send_chat_message_internal(text)


class TwitchChatClient(Client, ChatClient, ChatOutbound):
    def __init__(self, twitch_auth: TwitchAuth, settings: BotSettings, bot_id: str | None = None):
        self._twitch_auth = twitch_auth
        self._settings = settings
        self._command_router: PrefixCommandRouter | None = None
        self._chat_event_handler: ChatEventsHandler | None = None
        self.bot_nick = settings.bot_name
        self._prefix = settings.prefix
        self._channel_login = settings.channel_name

        self._token_user_id: str | None = None
        self._broadcaster_id: str | None = None
        self._subscribed_session_id: str | None = None
        self._has_active_subscription = False
        self._eventsub_lock = asyncio.Lock()

        super().__init__(
            client_id=twitch_auth.client_id,
            client_secret=twitch_auth.client_secret,
            bot_id=bot_id,
            fetch_client_user=bool(bot_id),
        )

    def set_router(self, router: CommandRouter) -> None:
        self._command_router = router

    def set_chat_event_handler(self, handler: ChatEventsHandler) -> None:
        self._chat_event_handler = handler

    async def setup_hook(self) -> None:
        await self._register_token()
        await self._ensure_broadcaster_id()
        await self._subscribe_chat_message_with_retry(reason="startup")

    async def stop(self) -> None:
        await super().close()

    async def event_ready(self) -> None:
        logger.info("TwitchChatClient ready. Broadcaster: %s", self._broadcaster_id or "unknown")

    async def event_message(self, payload: EventSubChatMessage) -> None:
        message_id = getattr(payload, "message_id", None)
        chatter = getattr(payload, "chatter", None)
        author = (chatter.display_name or chatter.name or "") if chatter else ""
        text_preview = (payload.text[:50] + "…") if len(payload.text) > 50 else payload.text
        logger.info(
            "EventSub event_message: message_id=%s author=%s text=%r subscribed_session=%s",
            message_id,
            author,
            text_preview,
            self._subscribed_session_id,
        )

        if not self._command_router:
            logger.error("CommandRouter is not set for TwitchChatClient")
            return

        if chatter is None:
            return

        author_name = chatter.display_name or chatter.name or ""
        chat_message = ChatMessage(author=author_name, text=payload.text, author_id=chatter.id)
        chat_ctx = _EventChatContext(self, channel_login=self._channel_login)

        handled = False
        try:
            handled = await self._command_router.dispatch(chat_message, chat_ctx)
        except Exception:
            logger.exception("Ошибка обработки сообщения: %s", payload.text)
        if handled:
            return

        if self._is_self_message(payload):
            return

        if payload.text.startswith(self._prefix):
            logger.debug("Неизвестная команда: %s", payload.text)
            return

        if self._chat_event_handler:
            try:
                await self._chat_event_handler.handle(
                    channel_name=self._channel_login,
                    display_name=chat_message.author,
                    message=payload.text,
                    bot_nick=self.bot_nick,
                )
            except Exception:
                logger.exception("Ошибка в ChatEventHandler для сообщения: %s", payload.text)

    async def event_websocket_welcome(self, payload: WebsocketWelcome) -> None:
        session_id = payload.id
        logger.info(
            "EventSub session_welcome: new_session_id=%s current_subscribed_session=%s has_active_sub=%s",
            session_id,
            self._subscribed_session_id,
            self._has_active_subscription,
        )
        if self._subscribed_session_id is None and self._has_active_subscription:
            self._subscribed_session_id = session_id
            logger.info("Привязали существующую подписку к session_id=%s", session_id)
            return

        if session_id == self._subscribed_session_id:
            logger.info("Подписка уже актуальна для session_id=%s", session_id)
            return

        if self._has_active_subscription:
            self._subscribed_session_id = session_id
            logger.info("EventSub реконнект: обновили session_id на %s (подписку восстанавливает TwitchIO)", session_id)
            return

        logger.info("EventSub welcome: подписываемся на новую сессию session_id=%s", session_id)
        await self._subscribe_chat_message_with_retry(session_id=session_id, reason="welcome")

    async def _register_token(self) -> None:
        if self._token_user_id:
            return
        try:
            validate = await self.add_token(self._twitch_auth.access_token, self._twitch_auth.refresh_token)
            self._token_user_id = validate.user_id
            if not self._token_user_id:
                logger.warning("Не удалось получить user_id из validate токена")
        except Exception:
            logger.exception("Не удалось добавить токен в TwitchIO Client"

    async def _ensure_broadcaster_id(self) -> None:
        if self._broadcaster_id:
            return

        if self._channel_login:
            try:
                users = await self.fetch_users(logins=[self._channel_login])
                if users:
                    self._broadcaster_id = users[0].id
            except Exception:
                logger.exception("Не удалось получить broadcaster_id по логину %s", self._channel_login)

        if not self._broadcaster_id and self._token_user_id:
            self._broadcaster_id = self._token_user_id

    async def _subscribe_chat_message(self) -> None:
        if not self._broadcaster_id or not self._token_user_id:
            raise RuntimeError(f"Нельзя подписаться на чат: broadcaster_id={self._broadcaster_id} token_user_id={self._token_user_id}")
        payload = ChatMessageSubscription(
            broadcaster_user_id=self._broadcaster_id,
            user_id=self._token_user_id,
        )
        await self.subscribe_websocket(payload, token_for=self._token_user_id)
        logger.info("Подписка на channel.chat.message оформлена для %s", self._broadcaster_id)

    async def _subscribe_chat_message_with_retry(self, session_id: str | None = None, reason: str = "unknown") -> None:
        logger.info(
            "EventSub _subscribe_chat_message_with_retry: reason=%s session_id=%s current_subscribed=%s has_active=%s",
            reason,
            session_id,
            self._subscribed_session_id,
            self._has_active_subscription,
        )
        async with self._eventsub_lock:
            if session_id and session_id == self._subscribed_session_id:
                logger.info("Подписка уже актуальна для session_id=%s", session_id)
                return

            delay = 1.0
            for attempt in range(1, 4):
                try:
                    await self._subscribe_chat_message()
                    self._has_active_subscription = True
                    if session_id:
                        self._subscribed_session_id = session_id
                    logger.info("Подписка EventSub восстановлена (%s) session_id=%s", reason, session_id)
                    return
                except HTTPException as e:
                    status = getattr(e, "status", None)
                    text = getattr(e, "text", None)
                    logger.warning(
                        "Попытка подписки %s/%s не удалась: status=%s text=%s",
                        attempt,
                        3,
                        status,
                        text,
                    )
                    if status not in {400, 409, 429, 500, 502, 503, 504}:
                        break
                except Exception:
                    logger.exception("Попытка подписки %s/%s завершилась ошибкой", attempt, 3)
                await asyncio.sleep(delay)
                delay *= 2

            logger.error("Не удалось восстановить подписку EventSub (%s)", reason)

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

    async def send_chat_message_internal(self, message: str) -> None:
        if not self._broadcaster_id or not self._token_user_id:
            logger.warning("Нельзя отправить сообщение: broadcaster_id=%s token_user_id=%s", self._broadcaster_id, self._token_user_id)
            return
        msg_preview = (message[:60] + "…") if len(message) > 60 else message
        logger.info("EventSub отправка в чат: subscribed_session=%s msg=%r", self._subscribed_session_id, msg_preview)
        for msg in self._split_text(message):
            try:
                await self._http.post_chat_message(
                    broadcaster_id=self._broadcaster_id,
                    sender_id=self._token_user_id,
                    message=msg,
                    token_for=self._token_user_id,
                )
                await asyncio.sleep(0.3)
            except HTTPException as e:
                logger.error(
                    "Ошибка отправки сообщения в чат: status=%s text=%s msg=%s",
                    getattr(e, "status", None),
                    getattr(e, "text", None),
                    msg,
                )
            except Exception:
                logger.exception("Ошибка отправки сообщения в чат: %s", msg)

    async def send_channel_message(self, channel_name: str, message: str) -> None:
        await self.send_chat_message_internal(message)

    async def post_message(self, message: str, chat_ctx: ChatContext) -> None:
        for msg in self._split_text(message):
            await chat_ctx.send_channel(msg)
            await asyncio.sleep(0.3)

    def _is_self_message(self, payload: EventSubChatMessage) -> bool:
        chatter = getattr(payload, "chatter", None)
        if chatter is None:
            return False
        if self._token_user_id and chatter.id == self._token_user_id:
            return True
        if chatter.name and chatter.name.lower() == (self.bot_nick or "").lower():
            return True
        return False
