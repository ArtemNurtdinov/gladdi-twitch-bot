from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.domain.model.rps import RPSGame
from app.minigame.infrastructure.minigame_repository import MinigameRepositoryImpl


class StartRpsGameUseCase:
    RPS_GAME_DURATION_MINUTES = 2
    RPS_BASE_BANK = 1500

    def __init__(
        self,
        minigame_repository: MinigameRepository,
        prefix: str,
        command_name: str,
        send_channel_message: Callable[[str, str], Awaitable[None]],
        minigame_uow: MinigameUnitOfWorkFactory,
        bot_name: str,
    ):
        self._minigame_repository = minigame_repository
        self._prefix = prefix
        self._command_name = command_name
        self._send_channel_message = send_channel_message
        self._minigame_uow = minigame_uow
        self._bot_name = bot_name

    async def start(self, channel_name: str):
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.RPS_GAME_DURATION_MINUTES)
        game = RPSGame(
            channel_name=channel_name,
            start_time=start_time,
            end_time=end_time,
            bank=self.RPS_BASE_BANK,
            is_active=True,
            winner_choice=None,
            user_choices={},
        )
        self._minigame_repository.save_active_rps_game(channel_name, game)

        game_message = (
            f"✊✌️🖐 НОВАЯ ИГРА КНБ! Банк старт: {self.RPS_BASE_BANK} монет + {MinigameRepositoryImpl.RPS_ENTRY_FEE_PER_USER}"
            f" за каждого участника. "
            f"Участвовать: {self._prefix}{self._command_name} <камень/ножницы/бумага> — "
            f"взнос {MinigameRepositoryImpl.RPS_ENTRY_FEE_PER_USER} монет. "
            f"Время на голосование: {self.RPS_GAME_DURATION_MINUTES} минуты ⏰"
        )

        await self._send_channel_message(channel_name, game_message)
        with self._minigame_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name, content=game_message, current_time=datetime.utcnow()
            )
