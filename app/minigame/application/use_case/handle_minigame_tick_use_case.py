import random
from datetime import datetime

from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.minigame.application.model.minigame_tick import MinigameTickDTO
from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.application.use_case.start_number_guess_game_use_case import StartNumberGuessGameUseCase
from app.minigame.application.use_case.start_rps_game_use_case import StartRpsGameUseCase
from app.minigame.application.use_case.start_word_game_use_case import StartWordGameUseCase
from app.minigame.domain.minigame_service import MinigameService


class HandleMinigameTickUseCase:
    DEFAULT_SLEEP_SECONDS = 60

    def __init__(
        self,
        minigame_service: MinigameService,
        minigame_orchestrator: MinigameOrchestrator,
        minigame_ouw: MinigameUnitOfWorkFactory,
        start_number_guess_game_use_case: StartNumberGuessGameUseCase,
        start_word_game_use_case: StartWordGameUseCase,
        start_rps_game_use_case: StartRpsGameUseCase,
    ):
        self._minigame_service = minigame_service
        self._minigame_orchestrator = minigame_orchestrator
        self._minigame_ouw = minigame_ouw
        self._start_number_guess_game_use_case = start_number_guess_game_use_case
        self._start_word_game_use_case = start_word_game_use_case
        self._start_rps_game_use_case = start_rps_game_use_case

    async def handle(self, minigame_tick: MinigameTickDTO) -> int:
        rps_game_complete_time = self._minigame_service.check_rps_game_complete_time(minigame_tick.channel_name, datetime.utcnow())
        if rps_game_complete_time:
            await self._minigame_orchestrator.finish_rps(minigame_tick.channel_name)
            return self.DEFAULT_SLEEP_SECONDS

        await self._minigame_orchestrator.finish_expired_games()

        with self._minigame_ouw.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(minigame_tick.channel_name)

        if not active_stream:
            return self.DEFAULT_SLEEP_SECONDS

        if not self._minigame_service.should_start_new_game(minigame_tick.channel_name):
            return self.DEFAULT_SLEEP_SECONDS

        choice = random.choice(["number", "word", "rps"])

        if choice == "word":
            await self._start_word_game_use_case.start(minigame_tick.channel_name)
        elif choice == "number":
            await self._start_number_guess_game_use_case.start(minigame_tick.channel_name)
        else:
            await self._start_rps_game_use_case.start(minigame_tick.channel_name)

        return self.DEFAULT_SLEEP_SECONDS
