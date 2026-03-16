import random
from datetime import datetime, timedelta

from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.application.use_case.finish_expired_games_use_case import FinishExpiredGamesUseCase
from app.minigame.application.use_case.finish_rps_use_case import FinishRpsUseCase
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.minigame.domain.minigame_repository import MinigameRepository


class HandleMinigameTickUseCase:
    FIRST_GAME_START_MIN = 15
    FIRST_GAME_START_MAX = 30
    GAME_START_INTERVAL_MIN = 30
    GAME_START_INTERVAL_MAX = 60

    def __init__(
        self,
        minigame_repository: MinigameRepository,
        minigame_ouw: MinigameUnitOfWorkFactory,
        start_number_guess_game_use_case: StartNumberGuessGameUseCase,
        start_word_game_use_case: StartWordGameUseCase,
        start_rps_game_use_case: StartRpsGameUseCase,
        finish_rps_game_use_case: FinishRpsUseCase,
        finish_expired_games_use_case: FinishExpiredGamesUseCase,
    ):
        self._minigame_repository = minigame_repository
        self._minigame_ouw = minigame_ouw
        self._start_number_guess_game_use_case = start_number_guess_game_use_case
        self._start_word_game_use_case = start_word_game_use_case
        self._start_rps_game_use_case = start_rps_game_use_case
        self._finish_rps_game_use_case = finish_rps_game_use_case
        self._finish_expired_games_use_case = finish_expired_games_use_case

    async def handle(self, channel_name: str):
        current_time = datetime.utcnow()
        active_rps_game = self._minigame_repository.get_active_rps_game(channel_name)

        if active_rps_game and active_rps_game.is_active and current_time > active_rps_game.end_time:
            await self._finish_rps_game_use_case.finish(channel_name)
            return

        await self._finish_expired_games_use_case.finish(channel_name)

        with self._minigame_ouw.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(channel_name)

        if not active_stream:
            return

        guess_game = self._minigame_repository.get_active_guess_game(channel_name)
        word_game = self._minigame_repository.get_active_word_game(channel_name)
        rps_game = self._minigame_repository.get_active_rps_game(channel_name)

        if guess_game or word_game or rps_game:
            return

        current_time = datetime.utcnow()
        last_game_time = self._minigame_repository.get_last_game_time(channel_name)

        if last_game_time:
            time_since_last = current_time - last_game_time
            random_minutes = random.randint(self.GAME_START_INTERVAL_MIN, self.GAME_START_INTERVAL_MAX)
            required_interval = timedelta(minutes=random_minutes)
            should_start_new_game = time_since_last >= required_interval
        else:
            stream_start_time = self._minigame_repository.get_stream_start_time(channel_name)
            if stream_start_time is None:
                stream_start_time = active_stream.started_at
            time_since_stream_start = current_time - stream_start_time
            first_game_delay_minutes = random.randint(self.FIRST_GAME_START_MIN, self.FIRST_GAME_START_MAX)
            required_delay = timedelta(minutes=first_game_delay_minutes)
            should_start_new_game = time_since_stream_start >= required_delay

        if not should_start_new_game:
            return

        choice = random.choice(["number", "word", "rps"])

        if choice == "word":
            await self._start_word_game_use_case.start(channel_name)
        elif choice == "number":
            await self._start_number_guess_game_use_case.start(channel_name)
        else:
            await self._start_rps_game_use_case.start(channel_name)
