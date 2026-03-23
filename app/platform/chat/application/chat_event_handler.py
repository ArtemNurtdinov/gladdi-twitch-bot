from datetime import datetime

from app.platform.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.platform.chat.application.model import ChatMessageDTO


class ChatEventsHandler:
    def __init__(self, handle_chat_message_use_case: HandleChatMessageUseCase):
        self._handle_chat_message_use_case = handle_chat_message_use_case

    async def handle(self, channel_name: str, display_name: str, message: str, bot_name: str) -> str | None:
        chat_message = ChatMessageDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            message=message,
            bot_nick=bot_name,
            occurred_at=datetime.utcnow(),
        )
        return await self._handle_chat_message_use_case.handle(chat_message)
