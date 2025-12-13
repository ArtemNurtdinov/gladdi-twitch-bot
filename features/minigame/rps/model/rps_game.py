from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


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

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.end_time

    def set_choice(self, user_name: str, choice: str) -> None:
        normalized = user_name.lower()
        self.user_choices[normalized] = choice

    def get_participants_count(self) -> int:
        return len(self.user_choices)

    def get_choice_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {c: 0 for c in RPS_CHOICES}
        for c in self.user_choices.values():
            if c in counts:
                counts[c] += 1
        return counts

    def get_winners(self) -> list[str]:
        if not self.winner_choice:
            return []
        return [user for user, choice in self.user_choices.items() if choice == self.winner_choice]

    def finish_game(self) -> None:
        self.is_active = False

    def timeout_game(self) -> None:
        self.is_active = False 