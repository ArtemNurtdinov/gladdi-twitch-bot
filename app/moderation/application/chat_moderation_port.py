from __future__ import annotations

from typing import Protocol


class ChatModerationPort(Protocol):
    async def timeout_user(self, channel_name: str, moderator_name: str, username: str, duration_seconds: int, reason: str) -> bool: ...
