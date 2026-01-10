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

    @property
    def author(self) -> str:
        author = getattr(self._ctx, "author", None)
        return getattr(author, "display_name", "") if author else ""

    async def reply(self, text: str) -> None:
        send = getattr(self._ctx, "send", None)
        if send:
            await send(text)
            return
        await self.send_channel(text)

    async def send_channel(self, text: str) -> None:
        channel = getattr(self._ctx, "channel", None)
        send = getattr(channel, "send", None) if channel else None
        if send:
            await send(text)
