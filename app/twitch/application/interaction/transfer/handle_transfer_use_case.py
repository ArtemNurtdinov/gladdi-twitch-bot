from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.twitch.application.interaction.transfer.model import TransferDTO
from core.provider import Provider


class HandleTransferUseCase:

    def __init__(
        self,
        economy_service_provider: Provider[EconomyService],
        chat_use_case_provider: Provider[ChatUseCase]
    ):
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        command_transfer: TransferDTO,
    ) -> str:
        command_prefix = command_transfer.command_prefix
        command_name = command_transfer.channel_name

        if not command_transfer.recipient_input or not command_transfer.amount_input:
            result = (
                f"@{command_transfer.display_name}, используй: {command_prefix}{command_name} [никнейм] [сумма]. "
                f"Например: {command_transfer.command_prefix}{command_transfer.command_name} @ArtemNeFRiT 100"
            )
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.bot_nick,
                    content=result,
                    current_time=command_transfer.occurred_at
                )
            return result

        try:
            transfer_amount = int(command_transfer.amount_input)
        except ValueError:
            result = (
                f"@{command_transfer.display_name}, неверная сумма! Укажи число. "
                f"Например: {command_transfer.command_prefix}{command_transfer.command_name} {command_transfer.recipient_input} 100"
            )
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.bot_nick,
                    content=result,
                    current_time=command_transfer.occurred_at
                )
            return result

        if transfer_amount <= 0:
            result = f"@{command_transfer.display_name}, сумма должна быть больше 0!"
            with db_session_provider() as db:
                self._chat_use_case_provider.get(db).save_chat_message(
                    channel_name=command_transfer.channel_name,
                    user_name=command_transfer.bot_nick,
                    content=result,
                    current_time=command_transfer.occurred_at
                )
            return result

        recipient = command_transfer.recipient_input.lstrip('@')
        normalized_receiver_name = recipient.lower()

        with db_session_provider() as db:
            transfer_result = self._economy_service_provider.get(db).transfer_money(
                channel_name=command_transfer.channel_name,
                sender_name=command_transfer.user_name,
                receiver_name=normalized_receiver_name,
                amount=transfer_amount
            )

        if transfer_result.success:
            result = f"@{command_transfer.display_name} перевел {transfer_amount} монет пользователю @{recipient}! "
        else:
            result = f"@{command_transfer.display_name}, {transfer_result.message}"

        with db_session_provider() as db:
            self._chat_use_case_provider.get(db).save_chat_message(
                channel_name=command_transfer.channel_name,
                user_name=command_transfer.bot_nick,
                content=result,
                current_time=command_transfer.occurred_at
            )

        return result
