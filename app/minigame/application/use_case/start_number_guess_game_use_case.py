import random
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_repository import MinigameRepository
from app.minigame.domain.model.guess_number import GuessNumberGame


class StartNumberGuessGameUseCase:
    GUESS_GAME_DURATION_MINUTES = 5
    GUESS_GAME_PRIZE = 3000
    GUESS_MIN_NUMBER = 1
    GUESS_MAX_NUMBER = 100

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
        target_number = random.randint(self.GUESS_MIN_NUMBER, self.GUESS_MAX_NUMBER)

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.GUESS_GAME_DURATION_MINUTES)

        game = GuessNumberGame(
            channel_name=channel_name,
            target_number=target_number,
            start_time=start_time,
            end_time=end_time,
            min_number=self.GUESS_MIN_NUMBER,
            max_number=self.GUESS_MAX_NUMBER,
            prize_amount=self.GUESS_GAME_PRIZE,
        )

        self._minigame_repository.save_active_guess_number_game(channel_name, game)

        game_message = (
            f"🎯 НОВАЯ МИНИ-ИГРА! Угадай число от {game.min_number} до {game.max_number}! "
            f"Первый, кто угадает, получит приз до {self.GUESS_GAME_PRIZE} монет! "
            f"Используй: {self._prefix}{self._command_name} [число]. "
            f"Время на игру: {self.GUESS_GAME_DURATION_MINUTES} минут ⏰"
        )
        await self._send_channel_message(channel_name, game_message)
        with self._minigame_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name, content=game_message, current_time=datetime.utcnow()
            )
