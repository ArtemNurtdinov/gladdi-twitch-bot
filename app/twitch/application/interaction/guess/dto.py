from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.twitch.application.interaction.dto import ChatContextDTO


@dataclass(frozen=True)
class GuessNumberDTO:
    command_prefix: str
    command_guess: str
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    guess_input: Optional[str]


@dataclass(frozen=True)
class GuessLetterDTO:
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    letter_input: Optional[str]


@dataclass(frozen=True)
class GuessWordDTO:
    channel_name: str
    display_name: str
    user_name: str
    bot_nick: str
    occurred_at: datetime
    word_input: Optional[str]
