from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GuessNumberDTO:
    command_prefix: str
    command_guess: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    guess_input: str | None


@dataclass(frozen=True)
class GuessLetterDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    letter_input: str | None


@dataclass(frozen=True)
class GuessWordDTO:
    command_prefix: str
    command_name: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    word_input: str | None
