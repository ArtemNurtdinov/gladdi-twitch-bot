from dataclasses import dataclass

from app.platform.command.domain.command_router import CommandRouter
from app.platform.command.help.infrastructure.help_command_handler import HelpCommandHandler


@dataclass(frozen=True)
class CommandRegistryResult:
    router: CommandRouter
    help_command_handler: HelpCommandHandler
