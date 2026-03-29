import asyncio

from app.core.logger.domain.logger import Logger
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from core.background.task_runner import BackgroundTaskRunner


class MinigameTickJob:
    _MINIGAME_TICK_DELAY = 60
    name = "check_minigames"

    def __init__(self, channel_name: str, handle_minigame_tick_use_case: HandleMinigameTickUseCase, logger: Logger):
        self._channel_name = channel_name
        self._handle_minigame_tick_use_case = handle_minigame_tick_use_case
        self._logger = logger.create_child(__name__)

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                await self._handle_minigame_tick_use_case.handle(self._channel_name)
                await asyncio.sleep(self._MINIGAME_TICK_DELAY)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_exception("Ошибка при проверке минигр: %s", e)
                await asyncio.sleep(self._MINIGAME_TICK_DELAY)
