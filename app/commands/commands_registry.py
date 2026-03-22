from app.commands.guess.infrastructure.rps_command_handler import RpsCommandHandler


class CommandRegistry:
    def __init__(
        self,
        rps_command_handler: RpsCommandHandler,
    ):
        self.rps_command_handler = rps_command_handler
