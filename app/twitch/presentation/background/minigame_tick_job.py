import asyncio
import logging
from typing import Any

from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class MinigameTickJob:
    name = "check_minigames"

    def __init__(self, channel_name: str, minigame_orchestrator: MinigameOrchestrator, default_delay: int = 60):
        self._channel_name = channel_name
        self._minigame_orchestrator = minigame_orchestrator
        self._default_delay = default_delay

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                delay = await self._minigame_orchestrator.run_tick(self._channel_name)
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                logger.info("MinigameTickJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в MinigameTickJob: {e}")
                await asyncio.sleep(self._default_delay)
