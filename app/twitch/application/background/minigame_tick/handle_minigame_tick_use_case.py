from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.twitch.application.background.minigame_tick.dto import MinigameTickDTO


class HandleMinigameTickUseCase:

    def __init__(self, minigame_orchestrator: MinigameOrchestrator):
        self._minigame_orchestrator = minigame_orchestrator

    async def handle(self, dto: MinigameTickDTO) -> int:
        return await self._minigame_orchestrator.run_tick(dto.channel_name)
