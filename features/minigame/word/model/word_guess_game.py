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

    def __post_init__(self):
        self.target_word = self.target_word.strip().lower()

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.end_time

    def is_valid_letter_guess(self, guess: str) -> bool:
        return len(guess) == 1 and guess.isalpha()

    def is_correct_word_guess(self, guess: str) -> bool:
        return guess.strip().lower() == self.target_word

    def reveal_letter(self, letter: str) -> bool:
        letter = letter.lower()
        if letter in self.guessed_letters:
            return False
        if letter in self.target_word:
            self.guessed_letters.add(letter)
            return True
        return False

    def all_letters_revealed(self) -> bool:
        letters_in_word = {ch for ch in self.target_word if ch.isalpha()}
        return letters_in_word.issubset(self.guessed_letters)

    def finish_game(self, winner_name: str) -> None:
        self.is_active = False
        self.winner = winner_name
        self.winning_time = datetime.utcnow()

    def timeout_game(self) -> None:
        self.is_active = False

    def get_masked_word(self) -> str:
        masked_chars = [
            (ch if (not ch.isalpha()) or ch.lower() in self.guessed_letters else "_")
            for ch in self.target_word
        ]
        return " ".join(masked_chars)

    def get_time_left_seconds(self) -> int:
        if not self.is_active:
            return 0
        time_left = self.end_time - datetime.utcnow()
        return max(0, int(time_left.total_seconds()))

    def get_time_left_display(self) -> str:
        seconds_left = self.get_time_left_seconds()
        if seconds_left <= 0:
            return "время истекло"
        minutes = seconds_left // 60
        seconds = seconds_left % 60
        if minutes > 0:
            return f"{minutes}м {seconds}с"
        else:
            return f"{seconds}с"

    def get_game_summary(self) -> str:
        if self.winner:
            return f"🎉 Слово '{self.target_word}' угадал @{self.winner}! Выигрыш: {self.prize_amount} монет"
        elif not self.is_active:
            return f"⏰ Время истекло! Слово было '{self.target_word}'"
        else:
            letters_count = sum(1 for ch in self.target_word if ch.isalpha())
            return f"🔤 Угадайте слово из {letters_count} букв! Слово: {self.get_masked_word()}"