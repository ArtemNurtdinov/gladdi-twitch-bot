from app.commands.guess.application.guess_command_handler import GuessCommandHandler
from app.commands.guess.infrastructure.rps_command_handler import RpsCommandHandler
from app.commands.help.application.help_command_handler import HelpCommandHandler
from app.commands.stats.infrastructure.stats_command_handler import StatsCommandHandler


class CommandRegistry:
    def __init__(
        self,
        stats_command_handler: StatsCommandHandler,
        help_command_handler: HelpCommandHandler,
        guess_command_handler: GuessCommandHandler,
        rps_command_handler: RpsCommandHandler,
    ):
        self.stats_command_handler = stats_command_handler
        self.help_command_handler = help_command_handler
        self.guess_command_handler = guess_command_handler
        self.rps_command_handler = rps_command_handler
