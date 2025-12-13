from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


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
    
    def __post_init__(self):
        if self.target_number < self.min_number or self.target_number > self.max_number:
            raise ValueError(f"Загаданное число должно быть от {self.min_number} до {self.max_number}")
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.end_time
    
    def is_correct_guess(self, guess: int) -> bool:
        return guess == self.target_number
    
    def is_valid_guess(self, guess: int) -> bool:
        return self.min_number <= guess <= self.max_number
    
    def finish_game(self, winner_name: str) -> None:
        self.is_active = False
        self.winner = winner_name
        self.winning_time = datetime.utcnow()
    
    def timeout_game(self) -> None:
        self.is_active = False
    
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
            return f"🎉 Число {self.target_number} угадал @{self.winner}! Выигрыш: {self.prize_amount} монет"
        elif not self.is_active:
            return f"⏰ Время истекло! Загаданное число было {self.target_number}"
        else:
            return f"🎯 Угадайте число от {self.min_number} до {self.max_number}! Приз: {self.prize_amount} монет. Осталось: {self.get_time_left_display()}" 