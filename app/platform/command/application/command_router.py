from __future__ import annotations

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.domain.command_router import CommandRouter


class CommandRouterImpl(CommandRouter):
    def __init__(self, prefix: str):
        self._prefix = prefix
        self._handlers: dict[str, CommandHandler] = {}

    def register_command_handler(self, name: str, handler: CommandHandler) -> None:
        self._handlers[name.lower()] = handler

    def get_command_handler(self, message: str) -> CommandHandler | None:
        if not message.startswith(self._prefix):
            return None

        without_prefix = message[len(self._prefix) :].strip()

        if not without_prefix:
            return None

        parts = without_prefix.split(" ", 1)
        cmd_name = parts[0].lower()
        command_handler = self._handlers.get(cmd_name)

        return command_handler
