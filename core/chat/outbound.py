from __future__ import annotations

from typing import Protocol

from core.chat.interfaces import ChatContext


class ChatOutbound(Protocol):
    async def send_channel_message(self, channel_name: str, message: str) -> None: ...
    async def post_message(self, message: str, chat_ctx: ChatContext) -> None: ...
