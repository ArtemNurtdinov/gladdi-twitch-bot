from datetime import datetime
from typing import Callable, Any, Awaitable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from core.db import SessionLocal


class TransferCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        command_name: str,
        bot_nick_provider: Callable[[], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_name = command_name
        self.bot_nick_provider = bot_nick_provider
        self.post_message_fn = post_message_fn

    async def handle(self, channel_name: str, sender_display_name: str, ctx, recipient: str | None = None, amount: str | None = None):
        sender_user_name = sender_display_name.lower()
        bot_nick = self.bot_nick_provider().lower()

        if not recipient or not amount:
            result = (
                f"@{sender_display_name}, используй: {self.command_prefix}{self.command_name} [никнейм] [сумма]. "
                f"Например: {self.command_prefix}{self.command_name} @ArtemNeFRiT 100"
            )
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        try:
            transfer_amount = int(amount)
        except ValueError:
            result = (
                f"@{sender_display_name}, неверная сумма! Укажи число. "
                f"Например: {self.command_prefix}{self.command_name} {recipient} 100"
            )
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        if transfer_amount <= 0:
            result = f"@{sender_display_name}, сумма должна быть больше 0!"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
            await self.post_message_fn(result, ctx)
            return

        recipient = recipient.lstrip('@')

        normalized_receiver_name = recipient.lower()

        with SessionLocal.begin() as db:
            transfer_result = self._economy_service(db).transfer_money(
                channel_name, sender_user_name, normalized_receiver_name, transfer_amount
            )

        if transfer_result.success:
            result = f"@{sender_display_name} перевел {transfer_amount} монет пользователю @{recipient}! "
        else:
            result = f"@{sender_display_name}, {transfer_result.message}"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick, result, datetime.utcnow())
        await self.post_message_fn(result, ctx)
