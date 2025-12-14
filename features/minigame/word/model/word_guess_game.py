from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Set


@dataclass
class WordGuessGame:
    channel_name: str
    target_word: str
    hint: str
    start_time: datetime
    end_time: datetime
    prize_amount: int = 1000
    is_active: bool = True
    winner: Optional[str] = None
    winning_time: Optional[datetime] = None
    guessed_letters: Set[str] = field(default_factory=set)

    def get_masked_word(self) -> str:
        masked_chars = [
            (ch if (not ch.isalpha()) or ch.lower() in self.guessed_letters else "_")
            for ch in self.target_word
        ]
        return " ".join(masked_chars)