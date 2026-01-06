from __future__ import annotations

from typing import Protocol


class ModerationPort(Protocol):
    async def timeout_user(self, broadcaster_id: str, moderator_id: str, user_id: str, duration_seconds: int, reason: str) -> bool: ...
