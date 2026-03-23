from datetime import datetime

from app.platform.command.domain.command_handler import CommandHandler
from app.platform.command.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.platform.command.guess.application.model import GuessLetterDTO


class GuessLetterCommandHandlerImpl(CommandHandler):
    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        handle_guess_use_case: HandleGuessUseCase,
        bot_name: str,
    ):
        self._command_prefix = command_prefix
        self._command_name = command_name
        self._handle_guess_use_case = handle_guess_use_case
        self._bot_name = bot_name

    async def handle(self, channel_name: str, user_name: str, message: str) -> str:
        tail = message[len(self._command_prefix + self._command_name) :].strip()
        letter = tail or None

        guess_letter = GuessLetterDTO(
            command_prefix=self._command_prefix,
            command_name=self._command_name,
            channel_name=channel_name,
            display_name=user_name,
            user_name=user_name.lower(),
            bot_nick=self._bot_name.lower(),
            occurred_at=datetime.utcnow(),
            letter_input=letter,
        )

        return await self._handle_guess_use_case.handle_letter(guess_letter=guess_letter)
