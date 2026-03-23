from __future__ import annotations

import asyncio
import logging
from collections import deque

from twitchio import Client, WebsocketWelcome
from twitchio.eventsub import ChatMessageSubscription
from twitchio.models.eventsub_ import ChatMessage as EventSubChatMessage

from app.platform.auth.platform_auth import PlatformAuth
from app.platform.chat.application.chat_event_handler import ChatEventsHandler
from app.platform.chat.application.platform_chat_client import PlatformChatClient
from app.platform.command.domain.command_router import CommandRouter


class TwitchChatClient(Client, PlatformChatClient):
    TWITCH_MESSAGE_LENGTH_MAX = 500

    def __init__(
        self,
        auth: PlatformAuth,
        chat_events_handler: ChatEventsHandler,
        command_router: CommandRouter,
        channel_name: str,
        command_prefix: str,
        bot_id: str,
        bot_name: str,
    ):
        Client.__init__(self, client_id=auth.client_id, client_secret=auth.client_secret, bot_id=bot_id, fetch_client_user=False)
        PlatformChatClient.__init__(
            self,
            auth=auth,
            chat_events_handler=chat_events_handler,
            command_router=command_router,
            channel_name=channel_name,
            bot_name=bot_name,
            command_prefix=command_prefix,
        )

        self._token_user_id: str | None = None
        self._broadcaster_id: str | None = None
        self._subscribed_session_id: str | None = None
        self._has_active_subscription = False
        self._eventsub_lock = asyncio.Lock()

        self._startup_subscription_done = asyncio.Event()
        self._subscription_in_progress = False
        self._recent_message_ids = deque(maxlen=1000)

        self.logger = logging.getLogger(__name__)

    async def setup_hook(self) -> None:
        self.logger.info("setup_hook called")
        await self._register_token()
        await self._ensure_broadcaster_id()
        await self._subscribe_chat(reason="startup")

    async def _register_token(self) -> None:
        payload = await self.add_token(self.auth.access_token, self.auth.refresh_token)
        self._token_user_id = payload.user_id
        self.logger.info(f"set _token_user_id = {self._token_user_id}")

    async def _ensure_broadcaster_id(self) -> None:
        users = await self.fetch_users(logins=[self.channel_name])
        if users:
            self._broadcaster_id = users[0].id
            self.logger.info(f"set _broadcaster_id = {self._broadcaster_id}")

    async def _subscribe_chat_message(self) -> None:
        payload = ChatMessageSubscription(
            broadcaster_user_id=self._broadcaster_id,
            user_id=self._token_user_id,
        )
        self.logger.info(f"calling subscribe_websocket, broadcaster_user_id = {self._broadcaster_id}, user_id={self._token_user_id}")
        await self.subscribe_websocket(payload, token_for=self._token_user_id)

    async def _subscribe_chat(self, reason: str, session_id: str | None = None):
        self.logger.info(f"_subscribe_chat called, reason = {reason}")
        async with self._eventsub_lock:
            if self._subscription_in_progress:
                self.logger.info("subscription already in progress, don't need new one")
                return

            self._subscription_in_progress = True
            try:
                await self._subscribe_chat_message()
                self._has_active_subscription = True
                if session_id:
                    self._subscribed_session_id = session_id

                if reason == "startup":
                    self._startup_subscription_done.set()

            finally:
                self._subscription_in_progress = False

    async def start_chat(self):
        await super().start(with_adapter=False, load_tokens=False, save_tokens=False)

    async def stop_chat(self):
        await super().close()

    async def event_ready(self) -> None:
        self.logger.info("event_ready")
        pass

    async def event_message(self, payload: EventSubChatMessage) -> None:
        message_id = payload.id
        user_name = payload.chatter.display_name or payload.chatter.name
        message = payload.text

        if not message_id or not user_name:
            return

        if message_id in self._recent_message_ids:
            return

        self._recent_message_ids.append(message_id)

        await super().handle_message(user_name, message)

    async def event_websocket_welcome(self, payload: WebsocketWelcome) -> None:
        self.logger.info("event_websocket_welcome")
        session_id = payload.id
        old_session = self._subscribed_session_id

        if not self._has_active_subscription and self._subscribed_session_id is None:
            try:
                self.logger.info("has active subscription, but subscribed_session_id is None, wait 5 seconds")
                await asyncio.wait_for(self._startup_subscription_done.wait(), timeout=5.0)
            except TimeoutError:
                self.logger.info("timeout on waiting startup subscription...")
                pass

        async with self._eventsub_lock:
            if self._has_active_subscription and self._subscribed_session_id is None:
                self.logger.info(f"subscribed to session: {session_id}")
                self._subscribed_session_id = session_id
                return

            if self._has_active_subscription and old_session != session_id:
                self.logger.info("has active subscription, but session_id is different, resubscribing..")
                self._has_active_subscription = False
                asyncio.create_task(self._subscribe_chat(session_id=session_id, reason="reconnect"))
                return

            if session_id == self._subscribed_session_id:
                self.logger.info(f"has active subscription, session_id {session_id}")
                return

            if not self._has_active_subscription:
                self.logger.info("no active subscription, subscribing..")
                asyncio.create_task(self._subscribe_chat(session_id=session_id, reason="welcome"))

    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self.TWITCH_MESSAGE_LENGTH_MAX:
            return [text]

        messages: list[str] = []
        while text:
            if len(text) <= self.TWITCH_MESSAGE_LENGTH_MAX:
                messages.append(text)
                break
            split_pos = text.rfind(" ", 0, self.TWITCH_MESSAGE_LENGTH_MAX)
            if split_pos == -1:
                split_pos = self.TWITCH_MESSAGE_LENGTH_MAX
            part = text[:split_pos].strip()
            if part:
                messages.append(part)
            text = text[split_pos:].strip()
        return messages

    async def send_channel_message(self, message: str):
        if not self._broadcaster_id or not self._token_user_id:
            return
        for msg in self._split_text(message):
            try:
                await self._http.post_chat_message(
                    broadcaster_id=self._broadcaster_id,
                    sender_id=self._token_user_id,
                    message=msg,
                    token_for=self._token_user_id,
                )
                await asyncio.sleep(0.3)
            except Exception:
                pass
