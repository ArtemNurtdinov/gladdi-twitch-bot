from __future__ import annotations

from typing import Protocol


class ChatEventsHandler(Protocol):
    async def handle(self, channel_name: str, display_name: str, message: str, bot_name: str) -> None: ...
