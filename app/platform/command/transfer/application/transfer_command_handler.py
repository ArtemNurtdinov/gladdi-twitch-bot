from datetime import UTC, datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.transfer.application.handle_transfer_use_case import HandleTransferUseCase
from app.platform.command.transfer.application.model import TransferDTO


class TransferCommandHandler(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_transfer_use_case: HandleTransferUseCase,
    ):
        self.command_prefix = command_prefix
        self._handle_transfer_use_case = handle_transfer_use_case
        self.command_name = command_name
        self._bot_name: str | None = None

    def apply_bot_name(self, bot_name) -> None:
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        tail = message[len(self.command_prefix + self.command_name) :].strip()
        recipient = None
        amount = None
        if tail:
            parts = tail.split()
            if parts:
                recipient = parts[0]
                if len(parts) > 1:
                    amount = parts[1]

        transfer = TransferDTO(
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.now(UTC),
            recipient_input=recipient,
            amount_input=amount,
            command_prefix=self.command_prefix,
            command_name=self.command_name,
            message=message,
        )

        return await self._handle_transfer_use_case.handle(command_transfer=transfer)
