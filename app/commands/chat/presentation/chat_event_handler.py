from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.commands.chat.application.model import ChatMessageDTO
from core.chat.outbound import ChatEventsHandler


class DefaultChatEventsHandler(ChatEventsHandler):
    def __init__(
        self,
        handle_chat_message_use_case: HandleChatMessageUseCase,
        send_channel_message: Callable[[str], Awaitable[None]],
    ):
        self._handle_chat_message_use_case = handle_chat_message_use_case
        self._send_channel_message = send_channel_message

    async def handle(self, channel_name: str, display_name: str, message: str, bot_name: str):
        chat_message = ChatMessageDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            message=message,
            bot_nick=bot_name,
            occurred_at=datetime.utcnow(),
        )
        result = await self._handle_chat_message_use_case.handle(chat_message)

        if result:
            await self._send_channel_message(result)
