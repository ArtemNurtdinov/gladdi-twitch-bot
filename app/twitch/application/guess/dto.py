from dataclasses import dataclass
from typing import Optional

from app.twitch.application.dto import ChatContextDTO


@dataclass(frozen=True)
class GuessNumberDTO(ChatContextDTO):
    guess_input: Optional[str]
    command_prefix: str
    command_guess: str


@dataclass(frozen=True)
class GuessLetterDTO(ChatContextDTO):
    letter_input: Optional[str]


@dataclass(frozen=True)
class GuessWordDTO(ChatContextDTO):
    word_input: Optional[str]

