from __future__ import annotations

from core.chat.interfaces import ChatContext, ChatMessage, CommandHandler, CommandRouter


class PrefixCommandRouter(CommandRouter):
    def __init__(self, prefix: str):
        self._prefix = prefix
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, name: str, handler: CommandHandler) -> None:
        self._handlers[name.lower()] = handler

    async def dispatch(self, message: ChatMessage, ctx: ChatContext) -> bool:
        if not message.text.startswith(self._prefix):
            return False

        without_prefix = message.text[len(self._prefix) :].strip()
        if not without_prefix:
            return False
        parts = without_prefix.split(" ", 1)
        cmd_name = parts[0].lower()
        handler = self._handlers.get(cmd_name)
        if not handler:
            return False

        await handler(ctx, message)
        return True
