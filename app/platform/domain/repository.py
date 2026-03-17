from typing import Protocol


class PlatformRepository(Protocol):
    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool: ...

    async def get_stream_chatters(self, broadcaster_id: str, moderator_id: str) -> list[str]: ...
