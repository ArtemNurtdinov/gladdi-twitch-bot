from collections.abc import Awaitable, Callable
from datetime import datetime

from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_service import MinigameService


class StartRpsGameUseCase:
    def __init__(
        self,
        minigame_service: MinigameService,
        prefix: str,
        command_name: str,
        send_channel_message: Callable[[str, str], Awaitable[None]],
        minigame_uow: MinigameUnitOfWorkFactory,
        bot_name: str,
    ):
        self._minigame_service = minigame_service
        self._prefix = prefix
        self._command_name = command_name
        self._send_channel_message = send_channel_message
        self._minigame_uow = minigame_uow
        self._bot_name = bot_name

    async def start(self, channel_name: str):
        self._minigame_service.start_rps_game(channel_name)
        game_message = (
            f"✊✌️🖐 НОВАЯ ИГРА КНБ! Банк старт: {MinigameService.RPS_BASE_BANK} монет + {MinigameService.RPS_ENTRY_FEE_PER_USER}"
            f" за каждого участника. "
            f"Участвовать: {self._prefix}{self._command_name} <камень/ножницы/бумага> — "
            f"взнос {MinigameService.RPS_ENTRY_FEE_PER_USER} монет. "
            f"Время на голосование: {MinigameService.RPS_GAME_DURATION_MINUTES} минуты ⏰"
        )

        await self._send_channel_message(channel_name, game_message)
        with self._minigame_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name, content=game_message, current_time=datetime.utcnow()
            )
