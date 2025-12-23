import asyncio
import logging

from core.background_task_runner import BackgroundTaskRunner

logger = logging.getLogger(__name__)


class MinigameTickJob:
    name = "check_minigames"

    def __init__(self, initial_channels: list[str], minigame_orchestrator, default_delay: int = 60):
        self._initial_channels = initial_channels
        self._minigame_orchestrator = minigame_orchestrator
        self._default_delay = default_delay

    def register(self, runner: BackgroundTaskRunner) -> None:
        runner.register(self.name, self.run)

    async def run(self):
        while True:
            try:
                if not self._initial_channels:
                    logger.warning("Список каналов пуст в MinigameTickJob. Пропускаем проверку мини-игр.")
                    await asyncio.sleep(self._default_delay)
                    continue

                channel_name = self._initial_channels[0]
                delay = await self._minigame_orchestrator.run_tick(channel_name)
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                logger.info("MinigameTickJob cancelled")
                break
            except Exception as e:
                logger.error(f"Ошибка в MinigameTickJob: {e}")
                await asyncio.sleep(self._default_delay)

