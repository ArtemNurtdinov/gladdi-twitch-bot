from typing import Callable, ContextManager

from sqlalchemy.orm import Session

from app.chat.application.chat_use_case import ChatUseCase
from app.economy.domain.economy_service import EconomyService
from app.twitch.application.interaction.transfer.dto import TransferDTO


class HandleTransferUseCase:

    def __init__(
        self,
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
    ):
        self._economy_service_factory = economy_service_factory
        self._chat_use_case_factory = chat_use_case_factory

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        dto: TransferDTO,
    ) -> str:

        if not dto.recipient_input or not dto.amount_input:
            result = (
                f"@{dto.display_name}, используй: {dto.command_prefix}{dto.command_name} [никнейм] [сумма]. "
                f"Например: {dto.command_prefix}{dto.command_name} @ArtemNeFRiT 100"
            )
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result

        try:
            transfer_amount = int(dto.amount_input)
        except ValueError:
            result = (
                f"@{dto.display_name}, неверная сумма! Укажи число. "
                f"Например: {dto.command_prefix}{dto.command_name} {dto.recipient_input} 100"
            )
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result

        if transfer_amount <= 0:
            result = f"@{dto.display_name}, сумма должна быть больше 0!"
            with db_session_provider() as db:
                self._chat_use_case_factory(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)
            return result

        recipient = dto.recipient_input.lstrip('@')
        normalized_receiver_name = recipient.lower()

        with db_session_provider() as db:
            transfer_result = self._economy_service_factory(db).transfer_money(
                dto.channel_name, dto.user_name, normalized_receiver_name, transfer_amount
            )

        if transfer_result.success:
            result = f"@{dto.display_name} перевел {transfer_amount} монет пользователю @{recipient}! "
        else:
            result = f"@{dto.display_name}, {transfer_result.message}"

        with db_session_provider() as db:
            self._chat_use_case_factory(db).save_chat_message(dto.channel_name, dto.bot_nick, result, dto.occurred_at)

        return result
