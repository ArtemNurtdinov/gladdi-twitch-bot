from collections.abc import Awaitable, Callable
from datetime import datetime

from app.commands.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.commands.guess.application.model import GuessWordDTO
from app.platform.command.domain.command_handler import CommandHandler


class GuessWordCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_guess_use_case: HandleGuessUseCase,
        bot_name: str,
        post_message_fn: Callable[[str], Awaitable[None]],
    ):
        self._command_prefix = command_prefix
        self._command_name = command_name
        self._handle_guess_use_case = handle_guess_use_case
        self._bot_name = bot_name
        self.post_message_fn = post_message_fn

    async def handle_command(self, channel_name: str, user_name: str, user_message: str):
        tail = user_message[len(self._command_prefix + self._command_name) :].strip()
        word = tail or None

        guess_word = GuessWordDTO(
            command_prefix=self._command_prefix,
            command_name=self._command_name,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
            word_input=word,
        )

        message = await self._handle_guess_use_case.handle_word(guess_word=guess_word)
        await self.post_message_fn(message)
