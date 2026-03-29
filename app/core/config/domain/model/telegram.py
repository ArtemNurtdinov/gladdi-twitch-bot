from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    group_id: int
