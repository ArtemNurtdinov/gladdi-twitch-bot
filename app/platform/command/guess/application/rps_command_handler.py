from datetime import datetime

from app.minigame.application.model.rps import RpsDTO
from app.minigame.application.use_case.handle_rps_use_case import HandleRpsUseCase
from app.platform.command.domain.command_handler import CommandHandler


class RpsCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_rps_use_case: HandleRpsUseCase,
        bot_name: str,
    ):
        self._command_prefix = command_prefix
        self._command_name = command_name
        self._handle_rps_use_case = handle_rps_use_case
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        tail = message[len(self._command_prefix + self._command_name) :].strip()
        choice = tail or None
        rps = RpsDTO(
            command_name=self._command_name,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_name=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
            choice_input=choice,
            message=message,
        )

        return await self._handle_rps_use_case.handle(rps=rps)
