from dataclasses import dataclass


@dataclass
class StreamStatistics:
    total_messages: int
    unique_users: int
    top_user: str | None
    total_battles: int
    top_winner: str | None
