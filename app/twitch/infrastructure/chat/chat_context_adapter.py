from __future__ import annotations

from typing import Any

from core.chat.interfaces import ChatContext


class CtxChatContext(ChatContext):
    def __init__(self, ctx: Any):
        self._ctx = ctx

    @property
    def channel(self) -> str:
        channel = getattr(self._ctx, "channel", None)
        return getattr(channel, "name", "") if channel else ""

    async def send_channel(self, text: str) -> None:
        channel = getattr(self._ctx, "channel", None)
        send = getattr(channel, "send", None) if channel else None
        if send:
            await send(text)
