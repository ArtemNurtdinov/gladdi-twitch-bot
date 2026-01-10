from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.commands.transfer.handle_transfer_use_case import HandleTransferUseCase
from app.commands.transfer.model import TransferDTO
from core.chat.interfaces import ChatContext


class TransferCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        handle_transfer_use_case: HandleTransferUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        command_name: str,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self._handle_transfer_use_case = handle_transfer_use_case
        self._db_session_provider = db_session_provider
        self.command_name = command_name
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(
        self, channel_name: str, sender_display_name: str, chat_ctx: ChatContext, recipient: str | None = None, amount: str | None = None
    ):
        dto = TransferDTO(
            channel_name=channel_name,
            display_name=sender_display_name,
            user_name=sender_display_name.lower(),
            bot_nick=self.bot_nick_provider().lower(),
            occurred_at=datetime.utcnow(),
            recipient_input=recipient,
            amount_input=amount,
            command_prefix=self.command_prefix,
            command_name=self.command_name,
        )

        result = await self._handle_transfer_use_case.handle(db_session_provider=self._db_session_provider, command_transfer=dto)

        await self.post_message_fn(result, chat_ctx)
