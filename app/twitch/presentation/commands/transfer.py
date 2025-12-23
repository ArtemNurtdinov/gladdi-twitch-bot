from datetime import datetime
from typing import Callable

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from core.db import SessionLocal


class TransferCommandHandler:

    def __init__(
        self,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        command_name: str,
        prefix: str,
        nick_provider: Callable[[], str],
    ):
        self._economy_service = economy_service_factory
        self._chat_use_case = chat_use_case_factory
        self.command_name = command_name
        self.prefix = prefix
        self.nick_provider = nick_provider

    async def handle(self, ctx, recipient: str | None = None, amount: str | None = None):
        channel_name = ctx.channel.name
        sender_name = ctx.author.display_name
        bot_nick = self.nick_provider() or ""

        if not recipient or not amount:
            result = (
                f"@{sender_name}, используй: {self.prefix}{self.command_name} [никнейм] [сумма]. "
                f"Например: {self.prefix}{self.command_name} @ArtemNeFRiT 100"
            )
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        try:
            transfer_amount = int(amount)
        except ValueError:
            result = (
                f"@{sender_name}, неверная сумма! Укажи число. "
                f"Например: {self.prefix}{self.command_name} {recipient} 100"
            )
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if transfer_amount <= 0:
            result = f"@{sender_name}, сумма должна быть больше 0!"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        recipient = recipient.lstrip('@')

        normalized_sender_name = sender_name.lower()
        normalized_receiver_name = recipient.lower()

        with SessionLocal.begin() as db:
            transfer_result = self._economy_service(db).transfer_money(
                channel_name, normalized_sender_name, normalized_receiver_name, transfer_amount
            )

        if transfer_result.success:
            result = f"@{sender_name} перевел {transfer_amount} монет пользователю @{recipient}! "
        else:
            result = f"@{sender_name}, {transfer_result.message}"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
        await ctx.send(result)