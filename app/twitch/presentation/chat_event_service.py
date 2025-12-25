from datetime import datetime
from typing import Callable, Awaitable, ContextManager

from app.twitch.application.interaction.chat.dto import ChatMessageDTO
from app.twitch.application.interaction.chat.handle_chat_message_use_case import HandleChatMessageUseCase


class ChatEventHandler:

    def __init__(
        self,
        handle_chat_message_use_case: HandleChatMessageUseCase,
        db_session_provider: Callable[[], ContextManager],
        send_channel_message: Callable[[str, str], Awaitable[None]],
    ):
        self._handle_chat_message_use_case = handle_chat_message_use_case
        self._db_session_provider = db_session_provider
        self._send_channel_message = send_channel_message

    async def handle(self, channel_name: str, display_name: str, message: str, bot_nick: str):
        dto = ChatMessageDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            message=message,
            bot_nick=bot_nick,
            occurred_at=datetime.utcnow(),
        )
        result = await self._handle_chat_message_use_case.handle(self._db_session_provider, dto)
        if result:
            await self._send_channel_message(channel_name, result)
