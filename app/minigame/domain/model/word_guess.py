from dataclasses import dataclass
from datetime import datetime


@dataclass
class WordGuessGame:
    channel_name: str
    target_word: str
    hint: str
    start_time: datetime
    end_time: datetime
    prize_amount: int
    is_active: bool
    winner: str | None
    winning_time: datetime | None
    guessed_letters: set[str]

    def get_masked_word(self) -> str:
        masked_chars = [(ch if (not ch.isalpha()) or ch.lower() in self.guessed_letters else "_") for ch in self.target_word]
        return " ".join(masked_chars)
