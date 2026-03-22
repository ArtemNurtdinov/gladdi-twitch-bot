from app.commands.guess.application.guess_command_handler import GuessCommandHandler
from app.commands.guess.infrastructure.rps_command_handler import RpsCommandHandler


class CommandRegistry:
    def __init__(
        self,
        guess_command_handler: GuessCommandHandler,
        rps_command_handler: RpsCommandHandler,
    ):
        self.guess_command_handler = guess_command_handler
        self.rps_command_handler = rps_command_handler
