import random
from datetime import datetime

from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.application.use_case.finish_expired_games_use_case import FinishExpiredGamesUseCase
from app.minigame.application.use_case.finish_rps_use_case import FinishRpsUseCase
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.minigame.domain.minigame_service import MinigameService


class HandleMinigameTickUseCase:
    def __init__(
        self,
        minigame_service: MinigameService,
        minigame_ouw: MinigameUnitOfWorkFactory,
        start_number_guess_game_use_case: StartNumberGuessGameUseCase,
        start_word_game_use_case: StartWordGameUseCase,
        start_rps_game_use_case: StartRpsGameUseCase,
        finish_rps_game_use_case: FinishRpsUseCase,
        finish_expired_games_use_case: FinishExpiredGamesUseCase,
    ):
        self._minigame_service = minigame_service
        self._minigame_ouw = minigame_ouw
        self._start_number_guess_game_use_case = start_number_guess_game_use_case
        self._start_word_game_use_case = start_word_game_use_case
        self._start_rps_game_use_case = start_rps_game_use_case
        self._finish_rps_game_use_case = finish_rps_game_use_case
        self._finish_expired_games_use_case = finish_expired_games_use_case

    async def handle(self, channel_name: str):
        current_time = datetime.utcnow()
        active_rps_game = self._minigame_service.get_active_rps_game(channel_name)

        if active_rps_game and active_rps_game.is_active and current_time > active_rps_game.end_time:
            await self._finish_rps_game_use_case.finish(channel_name)
            return

        await self._finish_expired_games_use_case.finish(channel_name)

        with self._minigame_ouw.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(channel_name)

        if not active_stream:
            return

        if not self._minigame_service.should_start_new_game(channel_name):
            return

        choice = random.choice(["number", "word", "rps"])

        if choice == "word":
            await self._start_word_game_use_case.start(channel_name)
        elif choice == "number":
            await self._start_number_guess_game_use_case.start(channel_name)
        else:
            await self._start_rps_game_use_case.start(channel_name)
