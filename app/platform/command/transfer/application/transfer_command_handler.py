from datetime import datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.transfer.application.handle_transfer_use_case import HandleTransferUseCase
from app.platform.command.transfer.application.model import TransferDTO


class TransferCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        handle_transfer_use_case: HandleTransferUseCase,
        command_name: str,
        bot_nick: str,
    ):
        self.command_prefix = command_prefix
        self._handle_transfer_use_case = handle_transfer_use_case
        self.command_name = command_name
        self._bot_nick = bot_nick

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
            bot_nick=self._bot_nick.lower(),
            occurred_at=datetime.utcnow(),
            recipient_input=recipient,
            amount_input=amount,
            command_prefix=self.command_prefix,
            command_name=self.command_name,
        )

        return await self._handle_transfer_use_case.handle(command_transfer=transfer)
