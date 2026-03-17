from app.platform.domain.repository import PlatformRepository


class TimeoutUserUseCase:
    def __init__(self, platform_repository: PlatformRepository):
        self._platform_repository = platform_repository

    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool:
        return await self._platform_repository.timeout_user(broadcaster_id, moderator_id, user_id, duration_seconds, reason)
