from collections.abc import Awaitable, Callable
from datetime import datetime

from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_service import MinigameService


class FinishExpiredGamesUseCase:
    def __init__(
        self,
        minigame_service: MinigameService,
        send_channel_message: Callable[[str, str], Awaitable[None]],
        minigame_uow: MinigameUnitOfWorkFactory,
        bot_name: str,
    ):
        self._minigame_service = minigame_service
        self._send_channel_message = send_channel_message
        self._minigame_uow = minigame_uow
        self._bot_name = bot_name

    async def finish(self):
        expired_games = self._minigame_service.check_expired_games()
        for channel, timeout_message in expired_games.items():
            await self._send_channel_message(channel, timeout_message)
            with self._minigame_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=channel, user_name=self._bot_name, content=timeout_message, current_time=datetime.utcnow()
                )
