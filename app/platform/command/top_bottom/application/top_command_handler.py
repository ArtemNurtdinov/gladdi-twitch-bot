from datetime import datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.top_bottom.application.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.platform.command.top_bottom.application.model import TopDTO


class TopCommandHandlerImpl(CommandHandler):
    _TOP_LIMIT = 7
    _BOTTOM_LIMIT = 10

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_top_bottom_use_case: HandleTopBottomUseCase,
        bot_name: str,
    ):
        self.command_prefix = command_prefix
        self._command_name = command_name
        self._handle_top_bottom_use_case = handle_top_bottom_use_case
        self._bot_name = bot_name
        self.top_limit = self._TOP_LIMIT
        self.bottom_limit = self._BOTTOM_LIMIT

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        top = TopDTO(
            channel_name=channel_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
            limit=self.top_limit,
            message=message,
        )

        return await self._handle_top_bottom_use_case.handle_top(command_top=top)
