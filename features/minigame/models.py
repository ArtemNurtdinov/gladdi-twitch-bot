from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Optional, Set

@dataclass
class GuessNumberGame:
    channel_name: str
    target_number: int
    start_time: datetime
    end_time: datetime
    min_number: int = 1
    max_number: int = 100
    prize_amount: int = 1000
    is_active: bool = True
    winner: Optional[str] = None
    winning_time: Optional[datetime] = None


RPS_CHOICES = ("камень", "ножницы", "бумага")


@dataclass
class RPSGame:
    channel_name: str
    start_time: datetime
    end_time: datetime
    bank: int = 500
    is_active: bool = True
    winner_choice: Optional[str] = None
    user_choices: Dict[str, str] = field(default_factory=dict)


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