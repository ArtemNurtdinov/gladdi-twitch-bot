import asyncio
from datetime import datetime

from app.minigame.application.model.minigame_tick import MinigameTickDTO
from app.minigame.application.use_case.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from core.background.task_runner import BackgroundTaskRunner


class MinigameTickJob:
    _MINIGAME_TICK_DELAY = 60
    name = "check_minigames"

    def __init__(self, channel_name: str, handle_minigame_tick_use_case: HandleMinigameTickUseCase):
        self._channel_name = channel_name
        self._handle_minigame_tick_use_case = handle_minigame_tick_use_case

    def register(self, runner: BackgroundTaskRunner):
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                dto = MinigameTickDTO(
                    channel_name=self._channel_name,
                    occurred_at=datetime.utcnow(),
                )
                delay = await self._handle_minigame_tick_use_case.handle(dto)
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self._MINIGAME_TICK_DELAY)
