from __future__ import annotations

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.domain.command_router import CommandRouter


class PrefixCommandRouter(CommandRouter):
    def __init__(self, prefix: str):
        self._prefix = prefix
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, name: str, handler: CommandHandler) -> None:
        self._handlers[name.lower()] = handler

    async def dispatch_command_handler(self, channel_name: str, user_name: str, message: str) -> bool:
        if not message.startswith(self._prefix):
            return False

        without_prefix = message[len(self._prefix) :].strip()

        if not without_prefix:
            return False

        parts = without_prefix.split(" ", 1)
        cmd_name = parts[0].lower()
        command_handler = self._handlers.get(cmd_name)

        if not command_handler:
            return False

        await command_handler.handle_command(channel_name, user_name, message)
        return True
