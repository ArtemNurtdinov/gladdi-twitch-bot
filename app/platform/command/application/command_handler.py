from app.commands.commands_registry import CommandRegistry
from app.platform.command.domain.command_handler import CommandHandler


class TopHandler(CommandHandler):
    def __init__(self, registry: CommandRegistry):
        self._registry = registry

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        await self._registry.top_bottom_command_handler.handle_top(channel_name=channel_name, display_name=user_name)


class BottomHandler(CommandHandler):
    def __init__(self, registry: CommandRegistry):
        self._registry = registry

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        await self._registry.top_bottom_command_handler.handle_bottom(channel_name=channel_name, display_name=user_name)


class HelpHandler(CommandHandler):
    def __init__(self, registry: CommandRegistry):
        self._registry = registry

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        await self._registry.help_command_handler.handle(channel_name=channel_name, display_name=user_name)


class StatsHandler(CommandHandler):
    def __init__(self, registry: CommandRegistry):
        self._registry = registry

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        await self._registry.stats_command_handler.handle(channel_name=channel_name, display_name=user_name)


class GuessNumberHandler(CommandHandler):
    def __init__(self, registry: CommandRegistry, prefix: str, command_name: str):
        self._registry = registry
        self._prefix = prefix
        self._command_name = command_name

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        tail = user_message[len(self._prefix + self._command_name) :].strip()
        number = tail or None
        await self._registry.guess_command_handler.handle_guess_number(channel_name=channel_name, display_name=user_name, number=number)


class GuessLetterHandler(CommandHandler):
    def __init__(self, registry: CommandRegistry, prefix: str, command_name: str):
        self._registry = registry
        self._prefix = prefix
        self._command_name = command_name

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        tail = user_message[len(self._prefix + self._command_name) :].strip()
        letter = tail or None
        await self._registry.guess_command_handler.handle_guess_letter(channel_name=channel_name, display_name=user_name, letter=letter)


class GuessWordHandler(CommandHandler):
    def __init__(self, registry: CommandRegistry, prefix: str, command_name: str):
        self._registry = registry
        self._prefix = prefix
        self._command_name = command_name

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        tail = user_message[len(self._prefix + self._command_name) :].strip()
        word = tail or None
        await self._registry.guess_command_handler.handle_guess_word(channel_name=channel_name, display_name=user_name, word=word)


class RpsHandler(CommandHandler):
    def __init__(self, registry: CommandRegistry, prefix: str, command_name: str):
        self._registry = registry
        self._prefix = prefix
        self._command_name = command_name

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        tail = user_message[len(self._prefix + self._command_name) :].strip()
        choice = tail or None
        await self._registry.rps_command_handler.handle(channel_name=channel_name, display_name=user_name, choice=choice)
