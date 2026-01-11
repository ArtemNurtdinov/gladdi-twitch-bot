from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager
from datetime import datetime

from sqlalchemy.orm import Session

from app.commands.guess.handle_guess_use_case import HandleGuessUseCase
from app.commands.guess.model import GuessLetterDTO, GuessNumberDTO, GuessWordDTO
from core.chat.interfaces import ChatContext


class GuessCommandHandler:
    def __init__(
        self,
        command_prefix: str,
        command_guess: str,
        command_guess_letter: str,
        command_guess_word: str,
        handle_guess_use_case: HandleGuessUseCase,
        db_session_provider: Callable[[], AbstractContextManager[Session]],
        bot_nick: str,
        post_message_fn: Callable[[str, ChatContext], Awaitable[None]],
    ):
        self.command_prefix = command_prefix
        self.command_guess = command_guess
        self.command_guess_letter = command_guess_letter
        self.command_guess_word = command_guess_word
        self._handle_guess_use_case = handle_guess_use_case
        self._db_session_provider = db_session_provider
        self._bot_nick = bot_nick
        self.post_message_fn = post_message_fn

    async def handle_guess_number(self, channel_name: str, display_name: str, chat_ctx: ChatContext, number: str | None):
        dto = GuessNumberDTO(
            command_prefix=self.command_prefix,
            command_guess=self.command_guess,
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_nick.lower(),
            occurred_at=datetime.utcnow(),
            guess_input=number,
        )

        message = await self._handle_guess_use_case.handle_number(
            db_session_provider=self._db_session_provider,
            guess_number=dto,
        )
        await self.post_message_fn(message, chat_ctx)

    async def handle_guess_letter(self, channel_name: str, display_name: str, chat_ctx: ChatContext, letter: str | None):
        dto = GuessLetterDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_nick.lower(),
            occurred_at=datetime.utcnow(),
            letter_input=letter,
        )

        message = await self._handle_guess_use_case.handle_letter(
            db_session_provider=self._db_session_provider,
            guess_letter_dto=dto,
        )
        await self.post_message_fn(message, chat_ctx)

    async def handle_guess_word(self, channel_name: str, display_name: str, chat_ctx: ChatContext, word: str | None):
        dto = GuessWordDTO(
            channel_name=channel_name,
            display_name=display_name,
            user_name=display_name.lower(),
            bot_nick=self._bot_nick.lower(),
            occurred_at=datetime.utcnow(),
            word_input=word,
        )

        message = await self._handle_guess_use_case.handle_word(db_session_provider=self._db_session_provider, guess_word_dto=dto)
        await self.post_message_fn(message, chat_ctx)
