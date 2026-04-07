import asyncio

from app.core.logger.domain.logger import Logger
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.task.domain.job import BackgroundJob


class MinigameTickJob(BackgroundJob):
    _MINIGAME_TICK_DELAY = 60
    name = "check_minigames"

    def __init__(self, handle_minigame_tick_use_case: HandleMinigameTickUseCase, logger: Logger):
        self._channel_name: str | None = None
        self._bot_name: str | None = None
        self._handle_minigame_tick_use_case = handle_minigame_tick_use_case
        self._logger = logger.create_child(__name__)

    def apply_channel(self, channel_name: str, bot_name: str):
        self._channel_name = channel_name
        self._bot_name = bot_name

    async def run(self):
        while True:
            try:
                await self._handle_minigame_tick_use_case.handle(self._channel_name, self._bot_name)
                await asyncio.sleep(self._MINIGAME_TICK_DELAY)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.log_exception("Ошибка при проверке минигр: %s", e)
                await asyncio.sleep(self._MINIGAME_TICK_DELAY)
